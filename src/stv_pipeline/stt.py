from stv_pipeline.helper import call

import base64
import numpy as np
import sounddevice as sd
import soundfile as sf


MODEL = "nvidia/nemotron-3.5-asr-streaming-multilingual-0.6b"  # cheap but accurate
RATE = 16000  # the sampling rate of the audio, i.e., 16kHz


def record(path="output/speech.wav"):
    """Record audio from the microphone and save it to a file.
    Args:
        path: The path to save the audio file.
    Returns:
        path: The path to the audio file.
    """
    chunks = []
    input("Press `Enter` to start recording...")
    # Record until the user presses `Enter` again
    # With sd.InputStream as the context manager, the callback function is called whenever a new chunk of speech is recorded
    with sd.InputStream(samplerate=RATE, channels=1, callback=lambda indata, *_: chunks.append(indata.copy())):  # *args
        input("Recording... Press `Enter` to stop.")
    sf.write(path, np.concatenate(chunks), RATE)
    return path


def transcribe(path):
    """Transcribe the audio file to text.
    Args:
        path: The path to the audio file.
    Returns:
        text: The transcribed text.
    """
    # Read the binary data of the audio file in bytes, encode it to base64 ASCII bytes, 
    # and decode to a string so that the POST request payload is in a valid format.
    audio = base64.b64encode(open(path, "rb").read()).decode()
    res = call("Transcribe", "/audio/transcriptions", {
        "model": MODEL, 
        "input_audio": {
            "data": audio, 
            "format": "wav", 
        }, 
    })
    return res["text"]


if __name__ == "__main__":
    path = record()
    text = transcribe(path)
    print(text)
    open("output/transcript.txt", "w", encoding="utf-8").write(text)