"""
Classifies a ticket's category and urgency using the finetuned
LoRA model served from the HF Space. Same input/output contract
as eval/baseline_classifier.py, so both can be through the same eval
harness for comparison.
"""

import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from eval.category import CATEGORIES, URGENCY_LEVELS


load_dotenv("env.local")

_client = None

def _get_client() -> OpenAI:
    """
    Create the client lazily, so importing this module never crashes
    if the URL is missing, this raises and intent_routing falls back to keyword
    matching.
    """
    global _client
    if _client is None:
        base_url = os.getenv("FINETUNED_MODEL_URL")
        if not base_url:
            raise RuntimeError("FINETUNED_MODEL_URL is not set")
        _client = OpenAI(
            base_url=base_url,
            api_key=os.getenv("FINETUNED_MODEL_API_KEY", "not-needed"),
            timeout=30,
            max_retries=1,
        )
    return _client




SYSTEM_PROMPT = f"""You are a support ticket classifier.
Classify the ticket into exactly one category from: {CATEGORIES}
And exactly one urgency level from: {URGENCY_LEVEL}
Respond ONLY with JSON in this exact format, no other text:
{{"category": "...", "urgency": "..."}}
"""



def classify_ticket_finetuned(body: str) -> dict:
    start = time.time()

    response = client.chat.completions.create(
        model="finetuned-llama-3-8b",   # llama.cpp server ignores this but he SDK requires it
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": body},
        ],
        temperature=0
    )

    latency_ms = (time.time() - start) * 1000
    raw = (response.choices[0].message.content or "").strip()


    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            parsed = {}
    except json.JSONDecodeError:
        parsed = {}

    category = parsed.get("category", "general")
    urgency = parsed.get("urgency", "normal")

    if category not in CATEGORIES:
        category = "general"
    if urgency not in URGENCY_LEVELS:
        urgency = "normal"

    usage = response.usage


    return {
        "category": category,
        "urgency": urgency,
        "latency_ms": latency_ms,
        "input_tokens": usage.prompt_tokens if usage else None,
        "output_tokens": usage.completion_tokens if usage else None,
    }
