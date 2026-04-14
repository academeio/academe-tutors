"""Tests for OpenRouter LLM service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.openrouter import stream_chat_response


@pytest.mark.asyncio
async def test_stream_chat_response_yields_deltas():
    """Should yield text deltas from OpenRouter streaming response."""
    mock_chunk_1 = MagicMock()
    mock_chunk_1.choices = [MagicMock()]
    mock_chunk_1.choices[0].delta.content = "Hello"

    mock_chunk_2 = MagicMock()
    mock_chunk_2.choices = [MagicMock()]
    mock_chunk_2.choices[0].delta.content = " world"

    mock_chunk_3 = MagicMock()
    mock_chunk_3.choices = [MagicMock()]
    mock_chunk_3.choices[0].delta.content = None

    async def mock_stream():
        for chunk in [mock_chunk_1, mock_chunk_2, mock_chunk_3]:
            yield chunk

    mock_response = MagicMock()
    mock_response.__aiter__ = lambda self: mock_stream()

    with patch("app.services.openrouter.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        deltas = []
        async for delta in stream_chat_response(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are a tutor.",
            api_key="test-key",
        ):
            deltas.append(delta)

    assert deltas == ["Hello", " world"]
