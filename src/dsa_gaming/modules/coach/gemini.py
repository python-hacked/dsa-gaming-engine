import asyncio

from google import genai
from google.genai import types

EMBED_MODEL = "gemini-embedding-001"
CHAT_MODELS = ("gemini-3.1-flash-lite", "gemini-3.8-flash")
EMBED_SIZE = 768


def _client(api_key: str) -> genai.Client:
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=20000, retry_options=types.HttpRetryOptions(attempts=1)),
    )


def _embed(api_key: str, text: str) -> list[float]:
    with _client(api_key) as client:
        response = client.models.embed_content(
            model=EMBED_MODEL,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=EMBED_SIZE),
        )
        values = list(response.embeddings[0].values)
    if len(values) != EMBED_SIZE:
        raise RuntimeError("Embedding size did not match the lesson store.")
    return values


def _complete(api_key: str, prompt: str) -> str:
    last_error = None
    with _client(api_key) as client:
        for model in CHAT_MODELS:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                    ),
                )
            except Exception as exc:
                last_error = exc
                continue
            text = (response.text or "").strip()
            if text:
                return text
    if last_error:
        raise last_error
    raise RuntimeError("The assistant returned an empty reply.")


async def embed_text(api_key: str, text: str) -> list[float]:
    return await asyncio.to_thread(_embed, api_key, text)


async def complete(api_key: str, prompt: str) -> str:
    return await asyncio.to_thread(_complete, api_key, prompt)
