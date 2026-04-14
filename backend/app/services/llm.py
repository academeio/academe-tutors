"""LLM service — Claude API integration for tutor responses."""

import anthropic
from app.core.config import settings


def get_client() -> anthropic.AsyncAnthropic:
    """Get async Anthropic client."""
    return anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


async def chat_with_rag(
    messages: list[dict],
    system_prompt: str,
    rag_context: str = "",
    model: str = "claude-opus-4-6",
    max_tokens: int = 16000,
):
    """Send a chat request to Claude with RAG context injected.

    Args:
        messages: Conversation history [{role, content}, ...]
        system_prompt: TutorBot soul template + instructions
        rag_context: Retrieved document chunks formatted as context
        model: Claude model ID
        max_tokens: Maximum response tokens

    Yields:
        Text deltas for streaming to the client.
    """
    client = get_client()

    full_system = system_prompt
    if rag_context:
        full_system += f"\n\n<retrieved_context>\n{rag_context}\n</retrieved_context>"

    async with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=full_system,
        thinking={"type": "adaptive"},
        messages=messages,
    ) as stream:
        async for event in stream:
            if event.type == "content_block_delta" and event.delta.type == "text_delta":
                yield event.delta.text
