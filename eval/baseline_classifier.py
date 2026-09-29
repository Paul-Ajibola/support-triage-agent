"""
baseline_classifier.py

classifies a ticket's category and urgency using a prompted
general-purpose model (Groq), used as the 'before'
comparison poitn against a fine-tuned model.
"""

import os
import json
import time
from groq import Groq
from dotenv import load_dotenv
from eval.category import CATEGORIES, URGENCY_LEVELS


load_dotenv(".env")


client = Groq(api_key=os.getenv("GROQ_API_KEY"))


SYSTEM_PROMPT = f"""You are a support ticket classifier.
Classify the ticket into exactly one category from: {CATEGORIES}
And  exactly one urgency level from {URGENCY_LEVELS}
Respond ONLY with JSON in this exact format, no other text:
{{"category": "...", "urgency": "..."}}
"""


def classify_ticket(body: str) -> dict:
    start = time.time()

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": body},
        ],
        temperature=0
    )

    latency_ms = (time.time() - start) * 1000
    raw = response.choices[0].message.content.strip()


    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"category": "general", "urgency": "normal"}

    usage = response.usage

    return {
        "category": parsed.get("category", "general"),
        "urgency": parsed.get("urgency", "normal"),
        "latency_ms": latency_ms,
        "input_tokens": usage.prompt_tokens,
        "output_tokens": usage.completion_tokens,
    }

