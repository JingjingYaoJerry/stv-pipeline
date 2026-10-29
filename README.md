## Speech-to-Video Pipeline

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-API-green.svg)](https://openrouter.ai/)
[![uv](https://img.shields.io/badge/uv-package%20manager-de5fe9.svg)](https://docs.astral.sh/uv/)

A small speech-to-video pipeline. It takes a typed sentence or a microphone recording, transcribes the recording when needed, asks a model for a short video plan, then generates a cover image, a voiceover, and a video — each step calling [OpenRouter](https://openrouter.ai/) and printing its cost.

---

### Key Features

* Record-or-type entry in `main.py`. Press Enter to record, or type a sentence to skip the microphone and speech-to-text.
* Speech-to-text in `stt.py` (`nvidia/nemotron-3.5-asr-streaming-multilingual-0.6b`). Audio is recorded at 16 kHz and sent as base64 WAV, so the JSON request body stays valid.
* Video plan in `script.py`. The model must return `script`, `image_prompt`, and `video_prompt`. `MODELS` tries `z-ai/glm-5.3`, then `deepseek/deepseek-v4-pro-0813`, and only providers that support the schema are used.
* Cover image in `image.py` (`bytedance-seed/seedream-5-0-flash`, 16:9). The image comes back as a base64 string and is decoded to `output/cover.png`.
* Voiceover in `voiceover.py` (`heygen/heygen-voice-1-turbo:free`, voice `nadine`). The speech endpoint returns raw PCM bytes (16-bit samples) at 44.1 kHz, which are saved as a WAV. The cost is read from the `X-Generation-Id` header, because this response has no JSON body.
* Video in `video.py` (`heygen/heygen-video-1`, 10 seconds, 480p). The cover is an optional first frame. Generation returns a job and is polled until it finishes, because it takes minutes rather than one response.
* Shared client in `helper.py`. `call` parses a JSON body. `post` is used when the body is audio bytes.
* A cost receipt in `main.py` after the run, in USD per step.
* Local tests in `tests/`. They replace the microphone and the HTTP calls, so `pytest` does not spend API credit.

The voiceover file and the video file are written separately. The video request does not upload `output/voiceover.wav`, so the soundtrack inside `output/video.mp4` is the one produced by the video model.

---

### Pipeline

```
main.py
   │
   ├── typed text, or record() → transcribe()
   ▼
write_script(text)
   │
   ├── generate_image()  → output/cover.png
   ├── speak()           → output/voiceover.wav
   └── generate_video()  → output/video.mp4
```

---

### Setup and Installation (PowerShell)

1. Clone the repository:

```powershell
git clone https://github.com/JingjingYaoJerry/stv-pipeline.git
cd stv-pipeline
```

2. Install [uv](https://docs.astral.sh/uv/) if you do not already have it, then sync dependencies from `pyproject.toml` / `uv.lock`:

```powershell
uv sync
```

3. Create a `.env` file at the repository root and add your OpenRouter API key:

```
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

Get a key at https://openrouter.ai/keys .

---

### Run the pipeline (CLI)

From the repository root. `output/` is created in the current directory.

```powershell
uv run python -m stv_pipeline
```

Or use the console script (same entry point):

```powershell
uv run stv-pipeline
```

Interaction:

- Type a sentence and press Enter → that sentence is the input. Recording and transcription are skipped.
- Press Enter with an empty line → record from the microphone. Press Enter again to stop. The WAV is then transcribed.
- The later steps run on their own and write `output/script.json`, `output/cover.png`, `output/voiceover.wav`, and `output/video.mp4`.
- When the video step is waiting, the status is printed about every 15 seconds.

Each step can also be run on its own, after the file it reads already exists:

```powershell
uv run python -m stv_pipeline.stt
uv run python -m stv_pipeline.script
uv run python -m stv_pipeline.image
uv run python -m stv_pipeline.voiceover
uv run python -m stv_pipeline.video
```

Run the tests (no microphone, no API calls):

```powershell
uv run pytest
```

---

### Project structure

```
stv-pipeline/
├── src/stv_pipeline/
│   ├── main.py            # Asks for text or a recording, then runs every step
│   ├── stt.py             # Microphone recording and transcription
│   ├── script.py          # Turns the text into script, image prompt, and video prompt
│   ├── image.py           # Cover image from image_prompt
│   ├── voiceover.py       # PCM speech response saved as WAV
│   ├── video.py           # Video job, polled, with the cover as the first frame
│   ├── helper.py          # OpenRouter client, cost tracking
│   ├── __init__.py        # Package marker
│   └── __main__.py        # python -m stv_pipeline
├── tests/
│   ├── test_helper.py     # Cost tracking and JSON vs failed HTTP responses
│   └── test_main.py       # Typed text skips recording; Enter records
├── pyproject.toml
├── uv.lock
└── README.md
```

---

### Acknowledgements

This project calls models through [OpenRouter](https://openrouter.ai/). Audio files are recorded and written with [sounddevice](https://python-sounddevice.readthedocs.io/) and [soundfile](https://python-soundfile.readthedocs.io/). Dependencies are installed with [uv](https://docs.astral.sh/uv/).
