from functools import lru_cache

from groq import Groq

from app.core.config import get_settings

# Groq's free tier hosts open-weight models at no cost, with generous request-
# per-minute limits — the reason it's the primary provider rather than a paid
# API. Llama 3.3 70B specifically: strong instruction-following for a "answer
# only from this context" prompt, without the cost of a proprietary frontier
# model, which this project's free/local-first constraint rules out anyway.
MODEL_NAME = "llama-3.3-70b-versatile"


@lru_cache
def _get_client() -> Groq:
    settings = get_settings()
    return Groq(api_key=settings.groq_api_key)


def generate_answer(*, system_prompt: str, user_prompt: str) -> str:
    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=800,
    )
    return response.choices[0].message.content
