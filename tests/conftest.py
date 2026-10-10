import pytest
import requests

from healstation.speech import response_audio


@pytest.fixture(autouse=True)
def isolate_api(monkeypatch, tmp_path):
    """Keep tests hermetic: no files in the real audio directory and no calls
    to an Ollama server that may be running on the developer's machine.
    Tests that exercise these paths override the patches themselves."""
    monkeypatch.setattr(response_audio, "AUDIO_OUTPUT_DIR", tmp_path / "audio_outputs")

    def _no_network(*args, **kwargs):
        raise requests.ConnectionError("network disabled in tests")

    monkeypatch.setattr(requests, "post", _no_network)


@pytest.fixture
def runtime(tmp_path):
    """An isolated v2 runtime: temporary data directory, throwaway key."""
    import api
    from healstation.runtime import Runtime
    from healstation.settings import Settings
    from healstation.store.crypto import new_key

    settings = Settings(data_dir=tmp_path / "data", kek_use_keyring=False, kek_auto_create=False)
    rt = Runtime(settings, kek=new_key())
    rt.start()
    api.app.state.runtime = rt
    yield rt
    rt.stop()
    api.app.state.runtime = None


@pytest.fixture
def client(runtime):
    from fastapi.testclient import TestClient

    import api

    return TestClient(api.app)
