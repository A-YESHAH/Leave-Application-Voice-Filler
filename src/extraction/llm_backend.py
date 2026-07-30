"""
LLM backend abstraction: uses local Ollama by default (dev/eval),
or Groq's hosted API when LLM_BACKEND=groq.
"""

import os

BACKEND = os.getenv("LLM_BACKEND", "ollama")

if BACKEND == "groq":
    from groq import Groq

    _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    GROQ_MODEL = os.getenv("GROQ_LLM_MODEL", "llama-3.1-8b-instant")
else:
    import ollama


def chat_json(messages: list[dict], model: str | None = None) -> str:
    """Send messages to the configured LLM and return raw JSON text."""

    if BACKEND == "groq":
        # Groq requires the conversation to explicitly mention JSON
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. "
                    "You must always respond with a valid JSON object only. "
                    "Do not include markdown or explanatory text."
                ),
            }
        ] + messages

        response = _client.chat.completions.create(
            model=model or GROQ_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
        )

        return response.choices[0].message.content

    else:
        response = ollama.chat(
            model=model or "llama3.2",
            messages=messages,
            format="json",
            options={"temperature": 0},
        )

        return response["message"]["content"]