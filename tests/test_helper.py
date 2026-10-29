from stv_pipeline import helper

import pytest


def setup_function():
    """Clear the costs dictionary before each test."""
    # pytest runs this before every test in the file, so one test's costs do not leak into the next
    helper.costs.clear()


def test_add_cost_stores_a_numeric_cost(capsys):
    """Test that add_cost stores a numeric cost.
    Args:
        capsys: pytest fixture to capture print output
    Returns:
        None
    """
    helper.add_cost("Transcribe", "nvidia/nemotron", 0.1)

    assert helper.costs["Transcribe (nvidia/nemotron)"] == 0.1
    # capsys catches print() for this test, so the text can be checked without looking at the terminal
    assert "$0.1000" in capsys.readouterr().out


def test_add_cost_prints_a_missing_cost_without_crashing(capsys):
    """Test that add_cost prints "N/A" when the cost is not a number without crashing.
    Args:
        capsys: pytest fixture to capture print output
    Returns:
        None
    """
    helper.add_cost("Voiceover", "heygen/heygen-voice-1-turbo:free", "N/A")

    assert helper.costs["Voiceover (heygen/heygen-voice-1-turbo:free)"] == "N/A"
    assert "N/A" in capsys.readouterr().out


def test_post_raises_when_the_api_rejects_the_request(monkeypatch):
    """Test that post raises an Exception when the API rejects the request.
    Args:
        monkeypatch: pytest fixture to monkeypatch (i.e. replace) the requests module
    Returns:
        None
    """
    class Response:
        ok = False
        status_code = 400
        text = "No models provided"

    # Replace requests.post for this test only
    monkeypatch.setattr(helper.requests, "post", lambda *args, **kwargs: Response())

    # The test passes only when post() raises an Exception whose message contains "400"
    with pytest.raises(Exception, match="400"):
        helper.post("/chat/completions", {})


def test_call_reads_the_json_body(monkeypatch):
    """Test that call reads the JSON body of the API response.
    Args:
        monkeypatch: pytest fixture to monkeypatch (i.e. replace) the requests module
    Returns:
        None
    """
    class Response:
        ok = True

        def json(self):
            return {"model": "z-ai/glm-5.3", "usage": {"cost": 0.0004}, "choices": []}

    monkeypatch.setattr(helper.requests, "post", lambda *args, **kwargs: Response())

    data = helper.call("Write Script", "/chat/completions", {"model": "z-ai/glm-5.3"})

    assert data["choices"] == []
    assert helper.costs["Write Script (z-ai/glm-5.3)"] == 0.0004
