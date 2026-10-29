from stv_pipeline.helper import API, call

import base64
import json
import requests


MODEL = "bytedance-seed/seedream-5-0-flash"


def generate_image(script):
    """Generate an image based on the script.
    Args:
        script: The script.
    Returns:
        image: The image.
    """
    res = call("Generate Image", "/images", {
        "model": MODEL,  # doesn't appear to support fallback chains
        "prompt": script["image_prompt"], 
        "aspect_ratio": "16:9", 
    })
    img_txt = res["data"][0]["b64_json"]  # images are returned as base64 encoded strings
    img_bytes = base64.b64decode(img_txt)  # decoding to real image bytes which can then be saved as a png file
    open("output/cover.png", "wb").write(img_bytes)  # render and save the image
    return "output/cover.png"


if __name__ == "__main__":
    models = requests.get(API + "/images/models").json()["data"]  # get all img-gen models supported by OpenRouter
    model = next(m for m in models if m["id"] == MODEL)  # gather all info about the selected model
    # print all supported parameters and their allowed values
    for setting, allowed in model["supported_parameters"].items():
        print(setting, allowed.get("values", ""))

    script = json.load(open("output/script.json", "r", encoding="utf-8"))
    print(generate_image(script))