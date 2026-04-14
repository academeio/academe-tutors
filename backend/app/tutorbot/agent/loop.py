"""Agent Loop — iterative LLM processing engine for tutor conversations.

Each user message triggers a loop:
1. Build context (history + RAG + student profile + competency map)
2. Call Claude with tools (RAG retrieval, web search, code execution)
3. Execute any tool calls
4. If more tools needed, loop back to step 2
5. Stream final response to client
6. Persist message and update student profile
"""

from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    """Configuration for a TutorBot agent instance."""

    model: str = "claude-opus-4-6"
    max_iterations: int = 20
    max_tool_result_chars: int = 16_000
    temperature: float = 0.7
    thinking: str = "adaptive"


@dataclass
class AgentContext:
    """Runtime context for an agent loop iteration."""

    session_id: str
    bot_id: str
    user_email: str
    user_role: str = "student"
    course_id: int | None = None
    competency_ids: list[int] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)
    rag_context: str = ""
    profile: dict = field(default_factory=dict)


class AgentLoop:
    """Iterative agent processing engine.

    Runs Claude in a tool-use loop until the model produces a final
    text response (stop_reason == "end_turn") or hits max_iterations.
    """

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()

    async def run(self, context: AgentContext, user_message: str):
        """Execute the agent loop for a single user message.

        Yields text deltas for streaming to the client.
        """
        # TODO: Implement full agent loop
        # 1. Append user message to history
        # 2. Build system prompt from soul template + context
        # 3. Retrieve RAG context from knowledge base
        # 4. Call Claude API with tools
        # 5. Handle tool calls (RAG search, web search, etc.)
        # 6. Loop until end_turn or max_iterations
        # 7. Yield text deltas
        # 8. Persist assistant message
        # 9. Update student profile (async, non-blocking)
        yield f"[AgentLoop placeholder] Processing: {user_message}"
