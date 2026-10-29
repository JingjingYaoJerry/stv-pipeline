from stv_pipeline.helper import HEADERS, add_cost, post

import base64
import json
import requests
import time


MODEL = "heygen/heygen-video-1"  # 50% off
DURATION = 10  # 5-15s, 
RESOLUTION = "480p"  # 480p, 768p, and 2K, 
# and can be steered with a first frame image according to the model docs


def generate_video(script, img_path):
    """Generate a video from script.json and cover.png.
    Args:
        script: The script.
        img_path: The path to the cover image.
    Returns:
        The path to the video.
    """
    # Convert the cover image into text so that it can be passed as a base64 encoded string in the POST request JSON payload
    img = base64.b64encode(open(img_path, "rb").read()).decode()
    # A job ID is returned for video generation as it's taking longer
    job = post("/videos", {
        "model": MODEL, 
        "prompt": script["video_prompt"], 
        "duration": DURATION, 
        "resolution": RESOLUTION, 
        "frame_images": [{
            "type": "image_url", 
            "image_url": {"url": "data:image/png;base64," + img}, 
            "frame_type": "first_frame", 
        }],  # the cover image is used as the first frame to steer which is completely optional
    }).json()
    
    # Check back every 15 seconds since it normally takes minutes to complete
    while job["status"] in ("pending", "in_progress"):
        print("Video is", job["status"])
        time.sleep(15)
        job = requests.get(job["polling_url"], headers=HEADERS).json()  # polling_url is the URL to check the status of the video generation job
    if job["status"] != "completed":
        raise Exception(f"Video generation failed: {job.get("error")}")

    vid = requests.get(job["unsigned_urls"][0], headers=HEADERS).content  # unsigned_urls is the URL to download the video
    open("output/video.mp4", "wb").write(vid)
    add_cost("Video Generation", MODEL, job["usage"]["cost"])
    return "output/video.mp4"


if __name__ == "__main__":
    script = json.load(open("output/script.json", "r", encoding="utf-8"))
    print(generate_video(script, "output/cover.png"))