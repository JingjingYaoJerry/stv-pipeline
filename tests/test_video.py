from stv_pipeline import helper
from stv_pipeline import video

import base64


def setup_function():
    """Clear the costs dictionary before each test."""
    helper.costs.clear()


def test_generate_video_sends_prompt_and_first_frame(monkeypatch, tmp_path):
    """Test that generate_video sends prompt, not input, and the cover as the first frame.
    Args:
        monkeypatch: pytest fixture to replace functions for this test only
        tmp_path: pytest fixture for a temporary folder that is deleted after the test
    Returns:
        None
    """
    # tmp_path is a temporary folder pytest deletes after the test
    cover = tmp_path / "cover.png"
    cover.write_bytes(b"png-bytes")
    sent = {}
    written = {}
    real_open = open

    class PostResponse:
        def json(self):
            return {
                "status": "completed",  # "completed" so the polling loop does not run in this test
                "unsigned_urls": ["https://example.test/video.mp4"],
                "usage": {"cost": 0.5},
            }

    def fake_post(path, payload):
        sent["path"] = path
        sent["payload"] = payload
        return PostResponse()

    class Download:
        content = b"mp4-bytes"

    def fake_open(path, mode="r", *args, **kwargs):
        if mode == "wb":
            # Catch the mp4 write. Reading the cover still uses the real open below
            class Handle:
                def write(self, data):
                    written["path"] = path
                    written["data"] = data
            return Handle()
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(video, "post", fake_post)
    monkeypatch.setattr(video.requests, "get", lambda url, headers=None: Download())
    monkeypatch.setattr(video, "open", fake_open, raising=False)  # open is a builtin

    result = video.generate_video({"video_prompt": "a waveform fades in"}, str(cover))

    payload = sent["payload"]
    assert sent["path"] == "/videos"
    # HeyGen rejects the request when this field is named "input"
    assert payload["prompt"] == "a waveform fades in"
    assert "input" not in payload
    assert payload["duration"] == 10
    assert payload["resolution"] == "480p"
    frame = payload["frame_images"][0]
    assert frame["frame_type"] == "first_frame"
    encoded = frame["image_url"]["url"].removeprefix("data:image/png;base64,")
    assert base64.b64decode(encoded) == b"png-bytes"
    assert written == {"path": "output/video.mp4", "data": b"mp4-bytes"}
    assert result == "output/video.mp4"
    assert helper.costs["Video Generation (heygen/heygen-video-1)"] == 0.5


def test_generate_video_polls_until_completed(monkeypatch, tmp_path):
    """Test that a pending video job is polled again after 15 seconds.
    Args:
        monkeypatch: pytest fixture to replace functions for this test only
        tmp_path: pytest fixture for a temporary folder that is deleted after the test
    Returns:
        None
    """
    cover = tmp_path / "cover.png"
    cover.write_bytes(b"png-bytes")
    sleeps = []
    real_open = open

    class PostResponse:
        def json(self):
            return {"status": "pending", "polling_url": "https://example.test/poll"}

    class Poll:
        def json(self):
            return {
                "status": "completed",
                "unsigned_urls": ["https://example.test/video.mp4"],
                "usage": {"cost": 0.1},
            }

    class Download:
        content = b"mp4-bytes"

    def fake_get(url, headers=None):
        # The same requests.get downloads the mp4 after the poll says the job is finished
        if url.endswith("/poll"):
            return Poll()
        return Download()

    monkeypatch.setattr(video, "post", lambda path, payload: PostResponse())
    monkeypatch.setattr(video.requests, "get", fake_get)
    # Record the wait instead of actually sleeping 15 seconds
    monkeypatch.setattr(video.time, "sleep", lambda seconds: sleeps.append(seconds))
    monkeypatch.setattr(video, "open", lambda path, mode="r", *args, **kwargs: real_open(path, mode, *args, **kwargs) if mode != "wb" else type("Handle", (), {"write": lambda self, data: None})(), raising=False)

    video.generate_video({"video_prompt": "wait"}, str(cover))

    assert sleeps == [15]
