"""PRIV-01 / PRIV-03: encrypted case store, blob format, key handling, erasure."""

import base64
import io
import shutil

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from healstation.settings import Settings
from healstation.store import crypto
from healstation.store.blobs import CHUNK_SIZE, HEADER_BYTES, BlobStore
from healstation.store.cases import CaseNotFound, CaseStore, new_id, normalize_abha_number
from healstation.store.crypto import CryptoError, KekSettings, KeyUnavailableError, load_kek
from healstation.store.db import Database
from healstation.store.keys import CaseKeyMissing, FieldSealer, KeyService
from healstation.store.models import Base

SENTINEL = "zebra-striped rash on my left elbow"


@pytest.fixture
def store(tmp_path):
    settings = Settings(data_dir=tmp_path / "data", kek_use_keyring=False)
    db = Database(settings.db_path)
    db.migrate()
    kek = crypto.new_key()
    keys = KeyService(kek)
    blobs = BlobStore(settings.data_dir)
    yield CaseStore(db, keys, blobs, settings), kek
    db.dispose()


@pytest.mark.parametrize("size", [0, 1, CHUNK_SIZE - 1, CHUNK_SIZE, CHUNK_SIZE + 1, int(CHUNK_SIZE * 3.5)])
def test_blob_round_trip_and_random_access(tmp_path, size):
    blobs = BlobStore(tmp_path)
    case_id, blob_id, key = new_id(), new_id(), crypto.new_key()
    data = bytes(i % 251 for i in range(size))
    blobs.write_bytes(case_id, blob_id, key, data)

    assert blobs.read_bytes(case_id, blob_id, key) == data
    with blobs.reader(case_id, blob_id, key) as reader:
        assert reader.size == size
        if size > 10:
            reader.seek(size - 10)
            assert reader.read() == data[-10:]
            reader.seek(size // 2)
            assert reader.read(7) == data[size // 2 : size // 2 + 7]
        reader.seek(0, io.SEEK_END)
        assert reader.read() == b""


def test_blob_is_ciphertext_and_wrong_key_fails(tmp_path):
    blobs = BlobStore(tmp_path)
    case_id, blob_id, key = new_id(), new_id(), crypto.new_key()
    blobs.write_bytes(case_id, blob_id, key, SENTINEL.encode() * 100)
    raw = blobs.path(case_id, blob_id).read_bytes()
    assert SENTINEL.encode() not in raw
    with pytest.raises(CryptoError):
        blobs.read_bytes(case_id, blob_id, crypto.new_key())


def test_blob_detects_truncation_and_tampering(tmp_path):
    blobs = BlobStore(tmp_path)
    case_id, blob_id, key = new_id(), new_id(), crypto.new_key()
    blobs.write_bytes(case_id, blob_id, key, b"x" * (CHUNK_SIZE * 3))
    path = blobs.path(case_id, blob_id)
    original = path.read_bytes()

    # Drop the final chunk: the new last chunk was not sealed as "last".
    path.write_bytes(original[: HEADER_BYTES + 2 * (CHUNK_SIZE + 16)])
    with pytest.raises(CryptoError):
        blobs.read_bytes(case_id, blob_id, key)

    tampered = bytearray(original)
    tampered[HEADER_BYTES + 100] ^= 0x01
    path.write_bytes(bytes(tampered))
    with pytest.raises(CryptoError):
        blobs.read_bytes(case_id, blob_id, key)


def test_blob_cannot_be_renamed_to_another_id(tmp_path):
    blobs = BlobStore(tmp_path)
    case_id, blob_id, other_id, key = new_id(), new_id(), new_id(), crypto.new_key()
    blobs.write_bytes(case_id, blob_id, key, b"secret")
    shutil.copy(blobs.path(case_id, blob_id), blobs.path(case_id, other_id))
    with pytest.raises(CryptoError):
        blobs.read_bytes(case_id, other_id, key)


def test_aborted_writer_leaves_no_file(tmp_path):
    blobs = BlobStore(tmp_path)
    case_id, blob_id, key = new_id(), new_id(), crypto.new_key()
    writer = blobs.writer(case_id, blob_id, key)
    writer.write(b"partial upload")
    writer.abort()
    assert list(blobs.case_dir(case_id).iterdir()) == []


def test_storage_ids_cannot_escape_the_data_directory(tmp_path):
    blobs = BlobStore(tmp_path)
    for bad in ("../../etc", "CON", "a" * 32 + "/x", "A" * 32, "x\x00y"):
        with pytest.raises(ValueError):
            blobs.path(new_id(), bad)
        with pytest.raises(ValueError):
            blobs.case_dir(bad)


def test_field_values_are_bound_to_their_row():
    key, case_id = crypto.new_key(), new_id()
    sealer = FieldSealer(key, case_id)
    sealed = sealer.seal_text("attachments.original_name", "row-1", "report.pdf")
    assert sealer.open_text("attachments.original_name", "row-1", sealed) == "report.pdf"
    with pytest.raises(CryptoError):
        sealer.open_text("attachments.original_name", "row-2", sealed)
    with pytest.raises(CryptoError):
        FieldSealer(key, new_id()).open_text("attachments.original_name", "row-1", sealed)


def test_database_holds_no_plaintext_clinical_content(store):
    cases, _kek = store
    case = cases.create(area=SENTINEL, abha_number="12-3456-7890-1234")
    sealer = cases.sealer(case.id)
    assert cases.details(case)["area"] == SENTINEL
    assert sealer.open_text("cases.area", case.id, case.area_enc) == SENTINEL

    cases.db.dispose()  # flush WAL into the main file
    on_disk = b"".join(p.read_bytes() for p in cases.settings.data_dir.rglob("*") if p.is_file())
    assert SENTINEL.encode() not in on_disk
    assert b"12-3456-7890-1234" not in on_disk


def test_losing_the_kek_makes_data_unreadable(store):
    cases, _kek = store
    case = cases.create(area=SENTINEL)
    other = CaseStore(cases.db, KeyService(crypto.new_key()), cases.blobs, cases.settings)
    with pytest.raises(CryptoError):
        other.key(case.id)


def test_erase_crypto_shreds_the_case(store):
    cases, kek = store
    case = cases.create(area=SENTINEL)
    key = cases.key(case.id)
    blob_id = new_id()
    cases.blobs.write_bytes(case.id, blob_id, key, SENTINEL.encode())
    sealed_area = case.area_enc
    db_copy = cases.db.path.read_bytes()

    assert cases.erase(case.id) is True
    assert not cases.blobs.case_dir(case.id).exists()
    with pytest.raises(CaseNotFound):
        cases.get(case.id)
    with pytest.raises(CaseKeyMissing):
        cases.key(case.id)
    # Even with the KEK and the old ciphertext, the destroyed case key is gone.
    with cases.db.session() as session:
        with pytest.raises(CaseKeyMissing):
            KeyService(kek).case_key(session, case.id)
    assert sealed_area is not None and SENTINEL.encode() not in db_copy
    assert cases.erase(case.id) is False


def test_migrations_match_the_models(store):
    cases, _kek = store
    with cases.db.engine.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert diff == []


def test_secure_delete_and_wal_are_enabled(store):
    cases, _kek = store
    with cases.db.engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA secure_delete").scalar() == 1
        assert connection.exec_driver_sql("PRAGMA journal_mode").scalar() == "wal"
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1


def test_abha_number_validation():
    assert normalize_abha_number("12345678901234") == "12-3456-7890-1234"
    assert normalize_abha_number("12-3456-7890-1234") == "12-3456-7890-1234"
    for bad in ("1234", "12-3456-7890-123X", "name@abdm"):
        with pytest.raises(ValueError):
            normalize_abha_number(bad)


def test_kek_loading_order_and_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(crypto, "_keyring", lambda: None)
    key = crypto.new_key()
    encoded = base64.b64encode(key).decode()
    assert load_kek(KekSettings(env_value=encoded)) == (key, "env")

    key_file = tmp_path / "secrets" / "kek.key"
    with pytest.raises(KeyUnavailableError):
        load_kek(KekSettings(file=key_file, auto_create=False))

    created, source = load_kek(KekSettings(file=key_file, auto_create=True))
    assert source == "file" and key_file.stat().st_mode & 0o077 == 0
    assert load_kek(KekSettings(file=key_file)) == (created, "file")

    with pytest.raises(KeyUnavailableError) as error:
        load_kek(KekSettings(env_value="not base64!"))
    assert "not base64" not in str(error.value)
    with pytest.raises(KeyUnavailableError):
        load_kek(KekSettings(env_value=base64.b64encode(b"short").decode()))
