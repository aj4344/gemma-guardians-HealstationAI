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
