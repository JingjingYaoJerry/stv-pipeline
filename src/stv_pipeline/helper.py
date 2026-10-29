from dotenv import load_dotenv

import os
import time
import requests


load_dotenv()
API = "https://openrouter.ai/api/v1"
HEADERS = {
    "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}", 
}
os.makedirs("output", exist_ok=True)

# The dictionary for tracking costs in USD in the following format: {step} ({model}) = ${cost:.2f}
costs = {}


def post(path, payload):
    """Make a POST request to the OpenRouter API.
    Args:
        path: The path to the API endpoint of models with different modalities.
        payload: The payload to send to the API, including the model, the input, and the output.
    Returns:
        The response from the API.
    """
    res = requests.post(API + path, headers=HEADERS, json=payload)
    if not res.ok:
        raise Exception(f"Request failed: {res.status_code} {res.text}")
    return res


def add_cost(step, model, cost):
    """Add the cost of a step to the costs dictionary.
    Args:
        step: The step of the process.
        model: The model used for the step.
        cost: The cost of the step.
    Returns:
        None
    """
    costs[f"{step} ({model})"] = cost
    if isinstance(cost, (int, float)):
        print(f"Cost for {step} ({model}) = ${cost:.4f}")
    else:
        print(f"Cost for {step} ({model}) = {cost}")


def call(step, path, payload):
    """Call a model with a given path and payload, and add the cost to the costs dictionary.
    Args:
        step: The step of the process.
        path: The path to the API endpoint of models with different modalities.
        payload: The payload to send to the API, including the model, the input, and the output.
    Returns:
        The parsed JSON body from the OpenRouter API.
    """
    res = post(path, payload)
    data = res.json()
    usage = data.get("usage", {})
    add_cost(step, data.get("model", payload.get("model")), usage.get("cost", "N/A"))
    return data


def lookup_cost(generation_id):
    """For responses with no JSON body (e.g., audio), look up the cost from the OpenRouter API by ID.
    Args:
        generation_id: The ID of the generation.
    Returns:
        The cost of the generation.
    """
    while True:  # to handle waiting situations under the synchronous implementation of the system
        res = requests.get(API + "/generation", headers=HEADERS, params={"id": generation_id})
        if res.ok:
            return res.json().get("data", {}).get("total_cost", "N/A")
        time.sleep(3)  # to avoid overwhelming the API with requests