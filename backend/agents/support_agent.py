"""Support agent: the autonomous AI loop for customer interactions.

Implements the full agentic cycle:
  1. Load conversation history from DB.
  2. Build system prompt from AgentConfig.
  3. Call Claude with the three available tools.
  4. If Claude requests a tool → execute it, feed the result back, repeat.
  5. When Claude produces a final text reply → save both the customer message
     and the agent reply to DB, then return the reply.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from supabase import Client

from agents.base_agent import BaseAgent
from config.prompts.support_agent import build_system_prompt
from database.models import AgentConfig, MessageRole
from integrations.llm_interfaces.base_llm_interface import BaseLLMInterface
from tools import escalation, knowledge, ticket

logger = logging.getLogger(__name__)

_TOOL_DEFINITIONS = [
    knowledge.TOOL_DEFINITION,
    ticket.TOOL_DEFINITION,
    escalation.TOOL_DEFINITION,
]

_MAX_ITERATIONS = 10
_FALLBACK_REPLY = (
    "Sorry, something went wrong while processing your request. "
    "Please try again in a moment or contact support directly."
)


class SupportAgent(BaseAgent):
    """Customer-support agent backed by Claude and three callable tools.

    Args:
        company_id: Tenant identifier used to scope DB queries and tool calls.
        agent_config: Configuration for this company's agent (name, tone, etc.).
        llm: An LLM interface instance (typically AnthropicInterface).
        supabase: Supabase client instance.
    """

    def __init__(
        self,
        company_id: UUID,
        agent_config: AgentConfig,
        llm: BaseLLMInterface,
        supabase: Client,
    ) -> None:
        super().__init__(name=agent_config.agent_name)
        self._company_id = company_id
        self._agent_config = agent_config
        self._llm = llm
        self._supabase = supabase

    # ------------------------------------------------------------------
    # Public entry point (implements BaseAgent.run)
    # ------------------------------------------------------------------

    async def run(self, input_data: dict) -> dict:
        """Process one customer turn and return the agent reply.

        Args:
            input_data: Dict with keys:
                - ``conversation_id`` (UUID): The active conversation.
                - ``content`` (str): The customer's message text.

        Returns:
            Dict with key ``reply`` (str): the final text reply from Claude.
        """
        conversation_id: UUID = input_data["conversation_id"]
        customer_content: str = input_data["content"]

        history = await self._load_history(conversation_id)
        messages: list[dict] = history + [
            {"role": "user", "content": customer_content}
        ]
        system_prompt = build_system_prompt(self._agent_config)

        reply = await self._run_loop(messages, system_prompt, conversation_id)

        await self._save_messages(conversation_id, customer_content, reply)
        return {"reply": reply}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _run_loop(
        self,
        messages: list[dict],
        system_prompt: str,
        conversation_id: UUID,
    ) -> str:
        """Agentic loop: call LLM → execute tools → repeat until final reply."""
        for iteration in range(_MAX_ITERATIONS):
            response = await self._llm.chat(
                messages,
                system=system_prompt,
                tools=_TOOL_DEFINITIONS,
            )

            if response.stop_reason != "tool_use" or not response.tool_uses:
                return response.text or _FALLBACK_REPLY

            logger.debug(
                "Iteration %d: executing %d tool(s): %s",
                iteration + 1,
                len(response.tool_uses),
                [t.name for t in response.tool_uses],
            )

            messages.append({"role": "assistant", "content": response.raw_content})

            tool_results: list[dict] = []
            for tool_use in response.tool_uses:
                result = await self._execute_tool(tool_use.name, tool_use.input, conversation_id)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": result,
                    }
                )
            messages.append({"role": "user", "content": tool_results})

        logger.warning(
            "SupportAgent hit max iterations (%d) for conversation %s",
            _MAX_ITERATIONS,
            conversation_id,
        )
        return _FALLBACK_REPLY

    async def _execute_tool(
        self,
        tool_name: str,
        tool_input: dict,
        conversation_id: UUID,
    ) -> str:
        """Dispatch a tool call by name and return its string result."""
        if tool_name == "search_knowledge":
            query = tool_input.get("query", "")
            if not query:
                logger.warning("search_knowledge called with missing 'query'")
                return "Error: missing 'query' parameter."
            return await knowledge.search_knowledge(
                query=query,
                company_id=self._company_id,
            )
        if tool_name == "create_ticket":
            subject = tool_input.get("subject", "")
            description = tool_input.get("description", "")
            if not subject or not description:
                logger.warning(
                    "create_ticket called with missing parameters: %s", tool_input
                )
                return "Error: missing parameters for the create_ticket tool."
            return await ticket.create_ticket(
                subject=subject,
                description=description,
                company_id=self._company_id,
                conversation_id=conversation_id,
                supabase=self._supabase,
            )
        if tool_name == "escalate":
            subject = tool_input.get("subject", "")
            description = tool_input.get("description", "")
            if not subject or not description:
                logger.warning(
                    "escalate called with missing parameters: %s", tool_input
                )
                return "Error: missing parameters for the escalate tool."
            return await escalation.escalate(
                subject=subject,
                description=description,
                company_id=self._company_id,
                conversation_id=conversation_id,
                supabase=self._supabase,
            )
        logger.error("SupportAgent called unknown tool: %s", tool_name)
        return f"Error: unknown tool '{tool_name}'."

    async def _load_history(self, conversation_id: UUID) -> list[dict]:
        """Load past messages for a conversation and convert to LLM format.

        MessageRole.CUSTOMER → "user"
        MessageRole.AGENT    → "assistant"
        MessageRole.SYSTEM   → skipped (handled in system prompt)
        """
        response = await asyncio.to_thread(
            lambda: self._supabase.table("messages")
            .select("role, content")
            .eq("conversation_id", str(conversation_id))
            .order("created_at")
            .execute()
        )
        role_map = {
            MessageRole.CUSTOMER: "user",
            MessageRole.AGENT: "assistant",
        }
        history: list[dict] = []
        for row in response.data or []:
            llm_role = role_map.get(row["role"])
            if llm_role:
                history.append({"role": llm_role, "content": row["content"]})
        return history

    async def _save_messages(
        self,
        conversation_id: UUID,
        customer_content: str,
        agent_reply: str,
    ) -> None:
        """Persist the customer message and the agent reply to the DB."""
        rows = [
            {
                "conversation_id": str(conversation_id),
                "role": MessageRole.CUSTOMER,
                "content": customer_content,
            },
            {
                "conversation_id": str(conversation_id),
                "role": MessageRole.AGENT,
                "content": agent_reply,
            },
        ]
        await asyncio.to_thread(
            lambda: self._supabase.table("messages").insert(rows).execute()
        )
