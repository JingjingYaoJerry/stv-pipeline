from stv_pipeline.helper import call

import json


MODELS = ["z-ai/glm-5.3", "deepseek/deepseek-v4-pro-0813"]  # fallback chain
PROMPT = "Turn this voice input into a short video.\n\nVoice input: "
# The exact shape/fields of output we want the model to fill and return.
SCHEMA = {
    "type": "object", 
    "properties": {
        "script": {"type": "string", "description": "A 40 ~ 60 word voiceover, with audio tags like [excited] or [whispers]"}, 
        "image_prompt": {"type": "string", "description": "A detailed prompt for a 16:9 cover image"}, 
        "video_prompt": {"type": "string", "description": "A 15-second clip that starts on the cover image: describe the motion"}, 
    }, 
    "required": ["script", "image_prompt", "video_prompt"], 
    "additionalProperties": False, 
}


def write_script(text):
    """Make the LLM write a script based on the voice input.
    Args:
        text: The voice input.
    Returns:
        script: The script.
    """
    res = call("Write Script", "/chat/completions", {
        "models": MODELS,  # OpenRouter API supports multiple models in a fallback chain
        "messages": [{"role": "user", "content": PROMPT + text}], 
        "response_format": {
            "type": "json_schema", 
            "json_schema": {"name": "video_plan", "strict": True, "schema": SCHEMA}, 
        }, 
        "provider": {"require_parameters": True},  # only use providers of the models that support the schema since OpenRouter has multiple providers for each model
    })
    return json.loads(res["choices"][0]["message"]["content"])


if __name__ == "__main__":
    text = open("output/transcript.txt", "r", encoding="utf-8").read()
    script = write_script(text)
    print(json.dumps(script, indent=4))
    json.dump(script, open("output/script.json", "w", encoding="utf-8"), indent=4)