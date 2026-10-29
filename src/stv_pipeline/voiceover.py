from stv_pipeline.helper import add_cost, lookup_cost, post

import json
import numpy as np
import soundfile as sf


MODEL = "heygen/heygen-voice-1-turbo:free"


def speak(script):
    res = post("/audio/speech", {
        "model": MODEL, 
        "input": script["script"], 
        "voice": "nadine", 
    })

    # TTS models tend to return raw PCM audio, which is just a raw stream of bytes (where every sample is a 16-bit integer)
    audio = np.frombuffer(res.content, dtype=np.int16)  # np.frombuffer() converts the raw bytes to a numpy array of int16 samples
    sf.write("output/voiceover.wav", audio, 44100)  # soundfile.write() saves the audio to a WAV file with 44.1 kHz mono PCM
    # The cost is instead stored in the headers
    add_cost("Voiceover Generation", MODEL, lookup_cost(res.headers["X-Generation-Id"]))
    return "output/voiceover.wav"


if __name__ == "__main__":
    script = json.load(open("output/script.json", "r", encoding="utf-8"))
    print(speak(script))