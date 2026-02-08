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
        conversation_log_file: str | None = None,
    ):
        self.test_case = test_case
        self.scenario: Dict = test_case["scenario"]
        self.persona: Dict = test_case["persona"]
        self.exec_config: Dict = test_case.get("execution_config", {})
        self.agent = agent_connector
        self.event_queue = event_queue
        self.use_ai_personas = use_ai_personas
        self.language = language
        self.conversation_log_file = conversation_log_file

        self.turns: List[ConversationTurn] = []
        self.chaos_events: List[ChaosEvent] = []

        # Metrics
        self.llm_calls = 0
        self.tokens_used = 0
        self.cost_usd = 0.0

        # Limits
        self.max_turns: int = self.exec_config.get("max_turns", 20)
        self.chaos_cfg: Dict = self.exec_config.get("chaos_injection", {})

        # Test info for logging
        self.test_number = test_case.get("test_number", 0)
        self.test_id = test_case.get("test_id", "unknown")

        # Goal-driven outcome tracking
        self.tool_sequence: List[str] = []
        self.tool_results_list: List[Dict[str, Any]] = []

        # Load terminal outcomes and tool chains from agent_map (if present)
        agent_map = test_case.get("agent_map", {})
        self.terminal_outcomes: List[Dict] = agent_map.get("terminal_outcomes", [])
        self.tool_chains: List[Dict] = agent_map.get("tool_chains", [])

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def run(self) -> Dict[str, Any]:
        """Execute the full conversation and return results dict."""
        await self.agent.reset()
        
        # Log conversation start with AI persona flag
        if self.conversation_log_file:
            self._log_conversation_start()

        user_message = await self._generate_persona_message(turn_number=1)

        turn_count = 0
        success = False
        failure_reason: Optional[str] = None
        outcome: Optional[str] = None

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
            user_turn = ConversationTurn(
                turn_number=turn_count,
                role="user",
                message=user_message,
                timestamp=turn_start,
                duration_ms=0,
            )
            self.turns.append(user_turn)
            self._log_conversation_turn(user_turn)

            # Record agent turn
            agent_turn = ConversationTurn(
                turn_number=turn_count,
                role="agent",
                message=agent_response["response"],
                tool_calls=agent_response.get("tool_calls", []),
                timestamp=turn_end,
                duration_ms=duration_ms,
            )
            self.turns.append(agent_turn)
            self._log_conversation_turn(agent_turn, tool_calls=agent_response.get("tool_calls", []))

            # Capture tool call results for chain validation
            for tc in agent_response.get("tool_calls", []):
                tool_name = tc.get("tool_name", "")
                self.tool_sequence.append(tool_name)
                result = tc.get("result")
                self.tool_results_list.append({
                    "tool_name": tool_name,
                    "arguments": tc.get("arguments"),
                    "result": result,
                    "success": result.get("status") == "ok" if isinstance(result, dict) else True,
                })

            # Check for terminal outcome (goal-driven)
            is_success, outcome_name = self._check_outcome()
            if is_success is not None:
                success = is_success
                outcome = outcome_name
                if not success and not failure_reason:
                    failure_reason = f"Terminal outcome: {outcome_name}"
                break

            # Check failure
            fail = self._check_failure()
            if fail:
                failure_reason = fail
                break

            # Persona gives up?
            if self._persona_gives_up(turn_count):
                failure_reason = f"Persona gave up after {turn_count} turns"
                outcome = "user_abandoned"
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
            "outcome": outcome,
            "tools_called_sequence": self.tool_sequence,
            "tool_results": self.tool_results_list,
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
        # First turn: use starter_openers from scenario if available
        if turn_number == 1:
            openers = self.scenario.get("starter_openers", [])
            if openers:
                msg = random.choice(openers)
                return self._apply_style(msg)

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
        """Goal-aware deterministic persona messages without AI calls.

        Messages reference the user_goal and adapt based on turn number
        so follow-ups are contextual rather than generic.
        """
        goal = self.scenario.get("user_goal", "get help")
        name = self.persona.get("name", "User")
        patience = self.persona.get("traits", {}).get("patience", 5)
        tlahuac = self.persona.get("tlahuac_data") or {}
        common_phrases = tlahuac.get("common_phrases", [])

        is_spanish = self.language.lower() in ("spanish", "español")

        if is_spanish:
            msg = self._offline_message_es(turn_number, goal, patience, common_phrases)
        else:
            msg = self._offline_message_en(turn_number, goal, patience)

        return self._apply_style(msg)

    def _offline_message_en(self, turn_number: int, goal: str, patience: int) -> str:
        """English offline messages, goal-aware by turn phase."""
        if turn_number == 1:
            return random.choice([
                f"Hi, I need help with: {goal}",
                f"Hello, I'm looking to {goal}",
                f"Hey, can you help me {goal}?",
            ])

        # Turn 2-3: provide details the agent asks for
        if turn_number <= 3:
            return random.choice([
                f"Sure, let me give you more details about {goal}.",
                f"Yes, that's right. I want to {goal}. What info do you need from me?",
                f"Correct. For context, my request is specifically about {goal}.",
                f"That works. What do you need from me to proceed with {goal}?",
            ])

        # Turn 4-5: push harder if no progress
        if turn_number <= 5:
            if patience <= 3:
                return random.choice([
                    f"I still need to {goal}. Can you help me with that now?",
                    f"We've been going back and forth. Can we just {goal} already?",
                    f"I'm getting impatient. I really just need to {goal}.",
                ])
            return random.choice([
                f"OK, so are we making progress on {goal}?",
                f"What else do you need from me to {goal}?",
                f"I'm still waiting to {goal}. What's the next step?",
            ])

        # Turn 6+: very impatient or wrapping up
        if patience <= 3:
            return random.choice([
                f"Can we just do {goal} already? This is taking forever.",
                f"I've explained everything. Please just {goal} now.",
                f"This is too slow. I just want to {goal}, nothing else.",
            ])
        return random.choice([
            f"Is there anything else you need to complete {goal}?",
            f"Let's wrap this up. Are we done with {goal}?",
            f"OK, what else is needed? I'm trying to {goal}.",
        ])

    def _offline_message_es(self, turn_number: int, goal: str, patience: int, common_phrases: List[str]) -> str:
        """Spanish offline messages, goal-aware by turn phase."""
        if turn_number == 1:
            openers = self.scenario.get("starter_openers", [])
            if openers:
                return random.choice(openers)
            return random.choice([
                f"Hola, necesito ayuda con: {goal}",
                f"Buenos días, estoy buscando {goal}",
                f"Hola, ¿puedes ayudarme con {goal}?",
            ])

        # Turn 2-3: provide details
        if turn_number <= 3:
            templates = [
                f"Sí, eso está bien. Quiero {goal}. ¿Qué necesitas de mí?",
                f"Correcto. Mi solicitud es sobre {goal}.",
                f"Perfecto. ¿Qué información necesitas para {goal}?",
            ]
            if common_phrases:
                templates.extend(common_phrases)
            return random.choice(templates)

        # Turn 4-5: push
        if turn_number <= 5:
            if patience <= 3:
                return random.choice([
                    f"Todavía necesito {goal}. ¿Puedes ayudarme ya?",
                    f"Llevamos rato. ¿Podemos simplemente {goal}?",
                    f"Me estoy frustrando. Solo necesito {goal}.",
                ])
            return random.choice([
                f"OK, ¿estamos avanzando con {goal}?",
                f"¿Qué más necesitas de mí para {goal}?",
                f"Sigo esperando para {goal}. ¿Cuál es el siguiente paso?",
            ])

        # Turn 6+
        if patience <= 3:
            return random.choice([
                f"¿Podemos simplemente {goal} ya? Esto toma mucho tiempo.",
                f"Ya expliqué todo. Por favor solo {goal} ahora.",
                f"Esto es muy lento. Solo quiero {goal}, nada más.",
            ])
        return random.choice([
            f"¿Hay algo más que necesites para completar {goal}?",
            f"Terminemos esto. ¿Ya estamos con {goal}?",
            f"OK, ¿qué más se necesita? Intento {goal}.",
        ])

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def _build_first_message_prompt(self) -> str:
        traits = self.persona.get("traits", {})
        style = self.persona.get("style", {})
        tlahuac = self.persona.get("tlahuac_data") or {}
        lang_instruction = f"\nIMPORTANT: Write your message in {self.language}." if self.language != "English" else ""

        # Enrich with tlahuac data when available
        persona_desc = ""
        if tlahuac:
            desc = tlahuac.get("description", "")
            persona_traits = tlahuac.get("persona_traits", [])
            common = tlahuac.get("common_phrases", [])
            if desc:
                persona_desc += f"Character: {desc}\n"
            if persona_traits:
                persona_desc += f"Personality traits: {', '.join(persona_traits)}\n"
            if common:
                persona_desc += f"Phrases you commonly use: {', '.join(common)}\n"

        return (
            f"You are roleplaying as a customer contacting a business.\n"
            f"Name: {self.persona.get('name', 'User')}\n"
            f"{persona_desc}"
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
        tlahuac = self.persona.get("tlahuac_data") or {}
        lang_instruction = f"\nIMPORTANT: Respond in {self.language}." if self.language != "English" else ""

        # Enrich with tlahuac data
        persona_context = ""
        if tlahuac:
            desc = tlahuac.get("description", "")
            persona_traits = tlahuac.get("persona_traits", [])
            common = tlahuac.get("common_phrases", [])
            if desc:
                persona_context += f"Character: {desc}\n"
            if persona_traits:
                persona_context += f"Personality: {', '.join(persona_traits)}\n"
            if common:
                persona_context += f"Phrases you naturally use: {', '.join(common)}\n"

        return (
            f"Continuing conversation as {self.persona.get('name', 'User')}:\n"
            f"{persona_context}"
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

    def _check_outcome(self) -> tuple[bool | None, str | None]:
        """Check if conversation has reached a terminal outcome.

        Returns ``(is_success, outcome_name)`` or ``(None, None)`` if not
        terminal yet.  Checked in order:

        1. Terminal outcomes from agent_map
        2. Tool chain completion
        3. Legacy success_conditions (backward compatible)
        """
        all_tool_names = set(self.tool_sequence)
        agent_text = ""
        if self.turns:
            agent_turns = [t for t in self.turns if t.role == "agent"]
            if agent_turns:
                agent_text = agent_turns[-1].message.lower()

        # --- 1. Terminal outcomes (from agent_map) ---
        for outcome in self.terminal_outcomes:
            signals = outcome.get("signals", {})
            required_tools = signals.get("required_tools", [])
            agent_confirms = signals.get("agent_confirms", False)

            tools_satisfied = all(t in all_tool_names for t in required_tools) if required_tools else False
            confirm_satisfied = not agent_confirms or self._agent_confirms(agent_text)

            if tools_satisfied and confirm_satisfied:
                return (outcome.get("is_success", True), outcome.get("name", "unknown"))

            # persona_gave_up is handled separately in the main loop
            if signals.get("persona_gave_up"):
                continue

        # --- 2. Tool chain completion ---
        for chain in self.tool_chains:
            sequence = chain.get("sequence", [])
            if not sequence:
                continue
            if self._chain_completed(sequence):
                return (True, f"chain:{chain.get('name', 'unknown')}")

        # --- 3. Legacy fallback: success_conditions ---
        conditions = self.scenario.get("success_conditions", {})

        # Single required tool
        required = conditions.get("tool_called")
        if required and required in all_tool_names:
            return (True, "legacy:tool_called")

        # Multiple required tools
        required_list = conditions.get("tools_called")
        if required_list and all(t in all_tool_names for t in required_list):
            return (True, "legacy:tools_called")

        # user_satisfied with enough exchanges
        if conditions.get("user_satisfied", False) and len(self.turns) >= 4:
            return (True, "legacy:user_satisfied")

        # --- Not terminal yet ---
        return (None, None)

    def _agent_confirms(self, agent_text: str) -> bool:
        """Heuristic: does the agent's last message sound like a confirmation?

        Uses custom confirmation_phrases from agent_map if provided,
        otherwise falls back to a default set of English/Spanish phrases.
        """
        # Allow agent_map to override confirmation phrases
        agent_map = self.test_case.get("agent_map", {})
        custom_phrases = agent_map.get("confirmation_phrases")
        if custom_phrases:
            return any(phrase.lower() in agent_text for phrase in custom_phrases)

        default_phrases = [
            "booked", "confirmed", "scheduled", "appointment", "created",
            "done", "completed", "all set", "taken care", "processed",
            "reserved", "set up", "arranged",
            # Spanish
            "reservado", "confirmado", "agendado", "listo", "completado",
            "programado", "creado", "procesado",
        ]
        return any(phrase in agent_text for phrase in default_phrases)

    def _chain_completed(self, expected_sequence: List[str]) -> bool:
        """Check if the expected tool sequence appears in order in tool_sequence."""
        seq_idx = 0
        for called in self.tool_sequence:
            if called == expected_sequence[seq_idx]:
                seq_idx += 1
                if seq_idx >= len(expected_sequence):
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

    # ------------------------------------------------------------------
    # Conversation logging
    # ------------------------------------------------------------------

    def _log_conversation_start(self) -> None:
        """Log conversation start metadata."""
        if not self.conversation_log_file:
            return
        
        import json
        from pathlib import Path
        
        log_path = Path(self.conversation_log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        log_entry = {
            "type": "conversation_start",
            "test_number": self.test_number,
            "test_id": self.test_id[:8],
            "scenario": self.scenario.get("title", "Unknown"),
            "persona": self.persona.get("name", "Unknown"),
            "uses_ai_personas": self.use_ai_personas,
            "language": self.language,
        }
        
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                f.flush()
        except Exception:
            pass

    def _log_conversation_turn(self, turn: ConversationTurn, tool_calls: List[Dict] = None) -> None:
        """Log conversation turn to file for real-time viewing."""
        if not self.conversation_log_file:
            return
        
        import json
        from pathlib import Path
        
        log_path = Path(self.conversation_log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        log_entry = {
            "type": "turn",
            "test_number": self.test_number,
            "test_id": self.test_id[:8],
            "scenario": self.scenario.get("title", "Unknown"),
            "persona": self.persona.get("name", "Unknown"),
            "turn": turn.turn_number,
            "role": turn.role,
            "message": turn.message,
            "tool_calls": tool_calls or turn.tool_calls,
            "timestamp": turn.timestamp.isoformat() if isinstance(turn.timestamp, datetime) else str(turn.timestamp),
            "duration_ms": turn.duration_ms,
        }
        
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                f.flush()  # Ensure immediate write
        except Exception:
            pass  # Don't fail tests if logging fails


def _calc_cost(usage) -> float:
    input_cost = (usage.input_tokens / 1_000_000) * _INPUT_COST_PER_M
    output_cost = (usage.output_tokens / 1_000_000) * _OUTPUT_COST_PER_M
    return input_cost + output_cost
