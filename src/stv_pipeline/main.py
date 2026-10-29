from .helper import costs
from .stt import record, transcribe
from .script import write_script
from .image import generate_image
from .voiceover import speak
from .video import generate_video


def print_cost_receipt():
    """Print the costs directory that's been tracking costs for each step of the pipeline.
    Args:
        None
    Returns:
        None
    """
    total = 0
    for step, cost in costs.items():
        if isinstance(cost, (int, float)):
            print(f"{step}: ${cost:.4f}")
            total += cost
        else:
            print(f"{step}: {cost}")
    print(f"Total: ${total:.4f}")


def main():
    # An option to skip the voice recording by providing text input directly
    text = input("Type text and press Enter, or press Enter to record: ").strip()
    if not text:
        voice = record()
        text = transcribe(voice)
    script = write_script(text)
    image = generate_image(script)
    voiceover = speak(script)
    video = generate_video(script, image)
    print_cost_receipt()


if __name__ == "__main__":
    main()