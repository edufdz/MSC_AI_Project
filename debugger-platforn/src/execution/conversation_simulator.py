"""
ConversationSimulator: drives a multi-turn conversation between a
synthetic persona and the agent under test.
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .agent_connector import AgentConnector
from .models import ChaosEvent, ConversationTurn

# Cost constants (Claude Haiku pricing per 1M tokens)
_INPUT_COST_PER_M = 1.00
_OUTPUT_COST_PER_M = 5.00


class ConversationSimulator:
    """
    Simulates a realistic multi-turn conversation for a single test case.

    Flow:
      1. Generate first persona message (AI or offline)
      2. Send to agent → receive response
      3. Check success / failure conditions
      4. Generate follow-up persona message
      5. Repeat until done, max_turns hit, or persona gives up
    """

    def __init__(
        self,
        test_case: Dict[str, Any],
        agent_connector: AgentConnector,
        event_queue: asyncio.Queue,
        use_ai_personas: bool = True,
        language: str = "English",
    ):
        self.test_case = test_case
        self.scenario: Dict = test_case["scenario"]
        self.persona: Dict = test_case["persona"]
        self.exec_config: Dict = test_case.get("execution_config", {})
        self.agent = agent_connector
        self.event_queue = event_queue
        self.use_ai_personas = use_ai_personas
        self.language = language

        self.turns: List[ConversationTurn] = []
        self.chaos_events: List[ChaosEvent] = []

        # Metrics
        self.llm_calls = 0
        self.tokens_used = 0
        self.cost_usd = 0.0

        # Limits
        self.max_turns: int = self.exec_config.get("max_turns", 20)
        self.chaos_cfg: Dict = self.exec_config.get("chaos_injection", {})

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def run(self) -> Dict[str, Any]:
        """Execute the full conversation and return results dict."""
        await self.agent.reset()

        user_message = await self._generate_persona_message(turn_number=1)

        turn_count = 0
        success = False
        failure_reason: Optional[str] = None

        while turn_count < self.max_turns:
            turn_count += 1
            turn_start = datetime.now(timezone.utc)

            # Inject chaos before agent call
            chaos_event = self._maybe_inject_chaos(turn_count)
            if chaos_event:
                self.chaos_events.append(chaos_event)
                if chaos_event.chaos_type == "timeout":
                    # Simulate timeout: skip agent call
                    self.turns.append(ConversationTurn(
                        turn_number=turn_count,
                        role="system",
                        message=f"[CHAOS] {chaos_event.description}",
                        timestamp=turn_start,
                        duration_ms=0,
                    ))
                    user_message = await self._generate_persona_message(
                        turn_number=turn_count + 1,
                        agent_last_response="[No response - timeout]",
                    )
                    continue

            # Send to agent
            agent_response = await self.agent.send_message(
                user_message,
                context={"turn": turn_count},
            )

            turn_end = datetime.now(timezone.utc)
            duration_ms = (turn_end - turn_start).total_seconds() * 1000

            if not agent_response["success"]:
                failure_reason = f"Agent error: {agent_response.get('error')}"
                self.turns.append(ConversationTurn(
                    turn_number=turn_count,
                    role="user",
                    message=user_message,
                    timestamp=turn_start,
                    duration_ms=duration_ms,
                ))
                break

            # Record user turn
            self.turns.append(ConversationTurn(
                turn_number=turn_count,
                role="user",
                message=user_message,
                timestamp=turn_start,
                duration_ms=0,
            ))

            # Record agent turn
            self.turns.append(ConversationTurn(
                turn_number=turn_count,
                role="agent",
                message=agent_response["response"],
                tool_calls=agent_response.get("tool_calls", []),
                timestamp=turn_end,
                duration_ms=duration_ms,
            ))

            # Check success
            if self._check_success():
                success = True
                break

            # Check failure
            fail = self._check_failure()
            if fail:
                failure_reason = fail
                break

            # Persona gives up?
            if self._persona_gives_up(turn_count):
                failure_reason = f"Persona gave up after {turn_count} turns"
                break

            # Generate next persona message
            user_message = await self._generate_persona_message(
                turn_number=turn_count + 1,
                agent_last_response=agent_response["response"],
            )

        if turn_count >= self.max_turns and not success:
            failure_reason = failure_reason or f"Max turns exceeded ({self.max_turns})"

        tool_calls_total = sum(
            len(t.tool_calls) for t in self.turns if t.role == "agent"
        )

        return {
            "success": success,
            "failure_reason": failure_reason,
            "turns": self.turns,
            "chaos_events": self.chaos_events,
            "llm_calls": self.llm_calls,
            "tool_calls_count": tool_calls_total,
            "tokens_used": self.tokens_used,
            "cost_usd": self.cost_usd,
        }

    # ------------------------------------------------------------------
    # Persona message generation
    # ------------------------------------------------------------------

    async def _generate_persona_message(
        self,
        turn_number: int,
        agent_last_response: str | None = None,
    ) -> str:
        if self.use_ai_personas:
            return await self._generate_ai_message(turn_number, agent_last_response)
        return self._generate_offline_message(turn_number, agent_last_response)

    async def _generate_ai_message(
        self,
        turn_number: int,
        agent_last_response: str | None,
    ) -> str:
        from anthropic import Anthropic

        client = Anthropic()

        if turn_number == 1:
            prompt = self._build_first_message_prompt()
        else:
            prompt = self._build_followup_prompt(agent_last_response or "")

        response = client.messages.create(
            model="claude-haiku-4-5",  # Switched to Haiku for cost savings (~67% cheaper)
            max_tokens=200,
            temperature=0.8,
            messages=[{"role": "user", "content": prompt}],
        )

        message = response.content[0].text.strip()
        message = self._apply_style(message)

        self.llm_calls += 1
        self.tokens_used += response.usage.input_tokens + response.usage.output_tokens
        self.cost_usd += _calc_cost(response.usage)

        return message

    def _generate_offline_message(
        self,
        turn_number: int,
        agent_last_response: str | None,
    ) -> str:
        """Deterministic persona messages without AI calls."""
        goal = self.scenario.get("user_goal", "get help")
        name = self.persona.get("name", "User")
        patience = self.persona.get("traits", {}).get("patience", 5)

        # Language-specific templates
        if self.language.lower() == "spanish" or self.language.lower() == "español":
            if turn_number == 1:
                templates = [
                    f"Hola, necesito ayuda con: {goal}",
                    f"Buenos días, estoy buscando {goal}",
                    f"Hola, ¿puedes ayudarme con {goal}?",
                ]
                msg = random.choice(templates)
            else:
                if patience <= 3 and turn_number > 3:
                    templates = [
                        "Esto está tomando demasiado tiempo. ¿Puedes hacerlo ya?",
                        "Ya expliqué lo que necesito. Por favor apúrate.",
                        "Me estoy frustrando. ¿Podemos terminar esto?",
                    ]
                elif turn_number > 5:
                    templates = [
                        "OK, ¿qué más necesitas de mí?",
                        "¿Hay algo más que necesites?",
                        "Continuemos. ¿Qué sigue?",
                    ]
                else:
                    templates = [
                        "Sí, eso está bien. Por favor continúa.",
                        "OK, suena bien. ¿Qué necesitas de mí?",
                        "Perfecto, adelante con eso.",
                        "Eso funciona. ¿Cuál es el siguiente paso?",
                    ]
                msg = random.choice(templates)
        else:
            # English (default)
            if turn_number == 1:
                templates = [
                    f"Hi, I need help with: {goal}",
                    f"Hello, I'm looking to {goal}",
                    f"Hey, can you help me {goal}?",
                ]
                msg = random.choice(templates)
            else:
                if patience <= 3 and turn_number > 3:
                    templates = [
                        "This is taking too long. Can you just do it?",
                        "I've already explained what I need. Please hurry.",
                        "I'm getting frustrated. Can we wrap this up?",
                    ]
                elif turn_number > 5:
                    templates = [
                        "OK, what else do you need from me?",
                        "Is there anything else required?",
                        "Let's continue. What's next?",
                    ]
                else:
                    templates = [
                        "Yes, that's correct. Please proceed.",
                        "OK, sounds good. What do you need from me?",
                        "Sure, go ahead with that.",
                        "That works. What's the next step?",
                    ]
                msg = random.choice(templates)

        return self._apply_style(msg)

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def _build_first_message_prompt(self) -> str:
        traits = self.persona.get("traits", {})
        style = self.persona.get("style", {})
        lang_instruction = f"\nIMPORTANT: Write your message in {self.language}." if self.language != "English" else ""
        return (
            f"You are roleplaying as a user with this personality:\n"
            f"Name: {self.persona.get('name', 'User')}\n"
            f"Patience: {traits.get('patience', 5)}/10\n"
            f"Clarity: {traits.get('clarity', 5)}/10\n"
            f"Tone: {style.get('tone', 'neutral')}\n\n"
            f"Your goal: {self.scenario.get('user_goal', 'get help')}\n"
            f"{lang_instruction}\n"
            f"Write your FIRST message to the agent. Be authentic to your personality.\n"
            f"Keep it short (1-3 sentences). Output ONLY the message, nothing else."
        )

    def _build_followup_prompt(self, agent_response: str) -> str:
        recent = self.turns[-6:]  # last 3 exchanges
        history_lines = []
        for t in recent:
            prefix = "You" if t.role == "user" else "Agent"
            history_lines.append(f"{prefix}: {t.message}")
        history = "\n".join(history_lines)

        traits = self.persona.get("traits", {})
        lang_instruction = f"\nIMPORTANT: Respond in {self.language}." if self.language != "English" else ""
        return (
            f"Continuing conversation as {self.persona.get('name', 'User')}:\n"
            f"Goal: {self.scenario.get('user_goal', 'get help')}\n"
            f"Patience: {traits.get('patience', 5)}/10\n"
            f"{lang_instruction}\n"
            f"Recent conversation:\n{history}\n\n"
            f"Agent just said: {agent_response}\n\n"
            f"What do you say next? Stay in character. 1-3 sentences.\n"
            f"Output ONLY your message, nothing else."
        )

    # ------------------------------------------------------------------
    # Style application
    # ------------------------------------------------------------------

    def _apply_style(self, message: str) -> str:
        style = self.persona.get("style", {})
        typo_rate = style.get("typo_rate", 0.0)
        abbrev = style.get("abbreviation_use", "low")

        # Typos
        if random.random() < typo_rate:
            words = message.split()
            if len(words) > 1:
                idx = random.randint(0, len(words) - 1)
                w = words[idx]
                if len(w) > 3:
                    chars = list(w)
                    pos = random.randint(1, len(chars) - 2)
                    chars[pos], chars[pos - 1] = chars[pos - 1], chars[pos]
                    words[idx] = "".join(chars)
                message = " ".join(words)

        # Abbreviations
        if abbrev == "high":
            message = (
                message.replace("you", "u")
                .replace("your", "ur")
                .replace("please", "pls")
                .replace("because", "cuz")
            )

        return message

    # ------------------------------------------------------------------
    # Success / failure checks
    # ------------------------------------------------------------------

    def _check_success(self) -> bool:
        conditions = self.scenario.get("success_conditions", {})

        all_tool_names = [
            tc.get("tool_name", "")
            for turn in self.turns
            if turn.role == "agent"
            for tc in turn.tool_calls
        ]

        # Single required tool
        required = conditions.get("tool_called")
        if required:
            return required in all_tool_names

        # Multiple required tools
        required_list = conditions.get("tools_called")
        if required_list:
            return all(t in all_tool_names for t in required_list)

        # Fallback: if user_satisfied is the only condition and we've had
        # at least 2 exchanges, consider it a success
        if conditions.get("user_satisfied", False) and len(self.turns) >= 4:
            return True

        return False

    def _check_failure(self) -> str | None:
        conditions = self.scenario.get("failure_conditions", {})

        if conditions.get("wrong_tool_called", False):
            forbidden = self.scenario.get("forbidden_tools", [])
            called = [
                tc.get("tool_name", "")
                for turn in self.turns
                if turn.role == "agent"
                for tc in turn.tool_calls
            ]
            for t in called:
                if t in forbidden:
                    return f"Forbidden tool called: {t}"

        return None

    def _persona_gives_up(self, turn_count: int) -> bool:
        patience = self.persona.get("traits", {}).get("patience", 5)
        edge = self.persona.get("edge_behaviors", {})
        rage_quits = edge.get("rage_quits", False)

        if rage_quits:
            quit_prob = (turn_count / self.max_turns) * (1 - patience / 10)
            return random.random() < quit_prob

        return False

    # ------------------------------------------------------------------
    # Chaos injection
    # ------------------------------------------------------------------

    def _maybe_inject_chaos(self, turn_number: int) -> ChaosEvent | None:
        if self.chaos_cfg.get("timeout") and random.random() < 0.15:
            return ChaosEvent(
                turn_number=turn_number,
                chaos_type="timeout",
                description="Injected timeout: agent did not respond",
            )

        if self.chaos_cfg.get("malformed_response") and random.random() < 0.1:
            return ChaosEvent(
                turn_number=turn_number,
                chaos_type="malformed_response",
                description="Injected malformed response from agent",
            )

        if self.chaos_cfg.get("data_conflict") and random.random() < 0.1:
            return ChaosEvent(
                turn_number=turn_number,
                chaos_type="data_conflict",
                description="Injected conflicting data in agent context",
            )

        return None


def _calc_cost(usage) -> float:
    input_cost = (usage.input_tokens / 1_000_000) * _INPUT_COST_PER_M
    output_cost = (usage.output_tokens / 1_000_000) * _OUTPUT_COST_PER_M
    return input_cost + output_cost
