"""Process-wide services for the v2 API: the case store, the job queue, the sweeper.

One Runtime per process (ADR-002). The app starts it at startup; tests build
their own with a temporary data directory and key.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from datetime import datetime

from fastapi import Request

from healstation.ingest.service import AttachmentService, StorageGuard
from healstation.settings import Settings
from healstation.store.blobs import BlobStore
from healstation.store.cases import CaseStore
from healstation.store.crypto import KekSettings, load_kek
from healstation.store.db import Database
from healstation.store.keys import KeyService
from healstation.store.models import utcnow

logger = logging.getLogger("healstation")


class Runtime:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        kek: bytes | None = None,
        clock: Callable[[], datetime] = utcnow,
    ):
        self.settings = settings or Settings()
        self.clock = clock
        self.settings.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        if kek is None:
            kek, source = load_kek(
                KekSettings(
                    env_value=self.settings.kek_env,
                    file=self.settings.kek_file,
                    use_keyring=self.settings.kek_use_keyring,
                    auto_create=self.settings.kek_auto_create,
                )
            )
            logger.info("Key-encryption key loaded", extra={"hs": {"kek_source": source}})
        self.db = Database(self.settings.db_path)
        self.db.migrate()
        self.keys = KeyService(kek)
        self.blobs = BlobStore(self.settings.data_dir)
        self.cases = CaseStore(self.db, self.keys, self.blobs, self.settings, clock=clock)
        self.storage = StorageGuard(self.settings, self.blobs.usage_bytes)
        self.attachments = AttachmentService(self.cases, self.settings, self.storage)
        self._started = False

    def start(self) -> None:
        self._started = True

    def stop(self) -> None:
        self._started = False
        self.db.dispose()


_runtime_lock = threading.Lock()


def get_runtime(request: Request) -> Runtime:
    """FastAPI dependency. Creates the process runtime on first use."""
    runtime = getattr(request.app.state, "runtime", None)
    if runtime is None:
        with _runtime_lock:
            runtime = getattr(request.app.state, "runtime", None)
            if runtime is None:
                runtime = Runtime()
                runtime.start()
                request.app.state.runtime = runtime
    return runtime
