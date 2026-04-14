"""OpenRouter LLM service — unified AI gateway via OpenAI-compatible API."""

from openai import AsyncOpenAI

from app.core.config import settings


def get_client(api_key: str | None = None) -> AsyncOpenAI:
    """Get an async OpenAI client pointed at OpenRouter."""
    return AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key or settings.openrouter_api_key,
        default_headers={
            "HTTP-Referer": "https://tutor.ai.in",
            "X-Title": "Academe Tutors",
        },
    )


async def stream_chat_response(
    messages: list[dict],
    system_prompt: str,
    api_key: str | None = None,
    model: str | None = None,
    max_tokens: int = 4096,
):
    """Stream a chat response from OpenRouter.

    Yields text deltas as they arrive.
    """
    client = get_client(api_key)
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    response = await client.chat.completions.create(
        model=model or settings.default_model,
        messages=full_messages,
        max_tokens=max_tokens,
        stream=True,
    )

    async for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
