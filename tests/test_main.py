import stv_pipeline.main as pipeline


def setup_function():
    """Clear the costs dictionary before each test."""
    # Same costs dict as helper.costs, cleared so the receipt test starts from empty
    pipeline.costs.clear()


def _stop_after_the_script(monkeypatch):
    """Replace the paid steps so main() can finish without calling those APIs.
    Args:
        monkeypatch: pytest fixture to replace functions for this test only
    Returns:
        None
    """
    # The later steps call paid APIs. These stand-ins let main() finish without generating anything
    monkeypatch.setattr(pipeline, "generate_image", lambda script: "output/cover.png")
    monkeypatch.setattr(pipeline, "speak", lambda script: "output/voiceover.wav")
    monkeypatch.setattr(pipeline, "generate_video", lambda script, image: "output/video.mp4")


def test_typed_text_skips_recording(monkeypatch):
    """Test that typed text is passed to write_script and recording is skipped.
    Args:
        monkeypatch: pytest fixture to replace functions for this test only
    Returns:
        None
    """
    seen = {}

    def record():
        raise AssertionError("should not record")

    def transcribe(path):
        raise AssertionError("should not transcribe")

    def write_script(text):
        seen["text"] = text

    # input is a builtin, so main.py does not already have an attribute with that name; raising=False is needed to replace it
    monkeypatch.setattr(pipeline, "input", lambda prompt: "This is a test", raising=False)
    monkeypatch.setattr(pipeline, "record", record)
    monkeypatch.setattr(pipeline, "transcribe", transcribe)
    monkeypatch.setattr(pipeline, "write_script", write_script)
    _stop_after_the_script(monkeypatch)

    pipeline.main()

    assert seen["text"] == "This is a test"


def test_pressing_enter_records_and_transcribes(monkeypatch):
    """Test that an empty line records audio and sends the transcript to write_script.
    Args:
        monkeypatch: pytest fixture to replace functions for this test only
    Returns:
        None
    """
    seen = {}

    def record():
        return "output/speech.wav"

    def transcribe(path):
        seen["path"] = path
        return "hello"

    def write_script(text):
        seen["text"] = text

    # Spaces only. main() strips them, treats the line as empty, and records
    monkeypatch.setattr(pipeline, "input", lambda prompt: "   ", raising=False)
    monkeypatch.setattr(pipeline, "record", record)
    monkeypatch.setattr(pipeline, "transcribe", transcribe)
    monkeypatch.setattr(pipeline, "write_script", write_script)
    _stop_after_the_script(monkeypatch)

    pipeline.main()

    assert seen["path"] == "output/speech.wav"
    assert seen["text"] == "hello"


def test_print_cost_receipt_sums_only_numbers(capsys):
    """Test that the cost receipt adds numeric costs and prints "N/A" as text.
    Args:
        capsys: pytest fixture to capture print output
    Returns:
        None
    """
    pipeline.costs["Transcribe (m)"] = 0.1
    pipeline.costs["Voiceover (m)"] = "N/A"
    pipeline.costs["Video (m)"] = 0.2

    pipeline.print_cost_receipt()

    receipt = capsys.readouterr().out
    assert "Transcribe (m): $0.1000" in receipt
    assert "Voiceover (m): N/A" in receipt
    # 0.1 + 0.2. "N/A" is printed, but it is not a number so it stays out of the total
    assert "Total: $0.3000" in receipt
