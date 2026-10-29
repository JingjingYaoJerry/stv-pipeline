import numpy as np

from stv_pipeline import helper
from stv_pipeline import voiceover


def setup_function():
    """Clear the costs dictionary before each test."""
    helper.costs.clear()


def test_speak_saves_pcm_at_44100_hz(monkeypatch):
    """Test that speak wraps the PCM bytes as a 44.1 kHz WAV.
    Args:
        monkeypatch: pytest fixture to replace functions for this test only
    Returns:
        None
    """
    # Three 16-bit samples, the same kind of bytes HeyGen puts in the response body
    samples = np.array([1, -2, 3], dtype=np.int16)
    sent = {}
    saved = {}

    class Response:
        content = samples.tobytes()
        headers = {"X-Generation-Id": "gen-tts-1"}

    def fake_post(path, payload):
        sent["path"] = path
        sent["payload"] = payload
        return Response()

    def fake_write(path, audio, rate):
        # Remember the arguments instead of writing output/voiceover.wav
        saved["path"] = path
        saved["audio"] = audio.copy()
        saved["rate"] = rate

    monkeypatch.setattr(voiceover, "post", fake_post)
    # lookup_cost would call GET /generation. Return a number so add_cost can still record it.
    monkeypatch.setattr(voiceover, "lookup_cost", lambda generation_id: 0)
    monkeypatch.setattr(voiceover.sf, "write", fake_write)

    result = voiceover.speak({"script": "Hello"})

    assert sent["path"] == "/audio/speech"
    assert sent["payload"]["input"] == "Hello"
    assert sent["payload"]["voice"] == "nadine"
    assert saved["path"] == "output/voiceover.wav"
    # HeyGen's PCM header says rate=44100. 24000 would play too slow
    assert saved["rate"] == 44100
    assert list(saved["audio"]) == [1, -2, 3]
    assert result == "output/voiceover.wav"
    assert helper.costs["Voiceover Generation (heygen/heygen-voice-1-turbo:free)"] == 0
