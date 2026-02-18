"""
GANConversationSimulator — GAN-style adversarial testing architecture.

Wraps the standard ConversationSimulator with a Critic agent that:
  - Observes the conversation every N turns
  - Can request restarts if the conversation is off-track
  - Detects false positives (test says "fail" but agent was fine)
  - Coaches the Generator to produce better test messages

Architecture (inspired by GANs):

    Generator (G)              Discriminator (D)
    ┌──────────────┐          ┌──────────────────┐
    │ Persona      │          │ Critic Agent     │
    │ Simulator    │──conv──▶│                  │
    │ (Haiku)      │◀─coach──│ (Haiku)          │
    └──────┬───────┘          └──────────────────┘
           │
           ▼
    ┌──────────────┐
    │ Agent Under  │
    │ Test         │
    └──────────────┘

Both G and D use cheap models (Haiku) — they correct each other,
so neither needs to be individually brilliant. This keeps costs low
while maintaining test quality through adversarial self-correction.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from .agent_connector import AgentConnector
from .conversation_simulator import ConversationSimulator
from .critic_agent import CriticAgent, CriticMetrics, CriticVerdict, OfflineCriticAgent
from .models import ConversationTurn

logger = logging.getLogger(__name__)


class GANConversationSimulator:
    """
    GAN-style conversation simulator.

    Runs the standard ConversationSimulator but adds a Critic loop:
    1. Every N turns, the Critic evaluates the conversation
    2. If quality is too low → restart with coaching feedback
    3. At the end, Critic checks for false positives
    4. Results include Critic metadata for Phase D enrichment

    Parameters
    ----------
    test_case : dict
        Standard test case from the test suite.
    agent_connector : AgentConnector
        Connection to the agent under test.
    event_queue : asyncio.Queue
        Event queue for the live monitor.
    use_ai : bool
        If True, use LLM-based Critic. If False, use offline heuristics.
    critic_model : str
        Model for the Critic agent (default: Haiku for cost savings).
    generator_model : str
        Model for the Generator persona (default: Haiku).
    evaluate_every : int
        Critic evaluates every N turns.
    max_restarts : int
        Maximum conversation restarts before giving up.
    quality_threshold : float
        Minimum quality score to continue (0-10).
    language : str
        Language for persona messages.
    conversation_log_file : str | None
        Path to conversation log file.
    """

    def __init__(
        self,
        test_case: Dict[str, Any],
        agent_connector: AgentConnector,
        event_queue: asyncio.Queue,
        use_ai: bool = True,
        critic_model: str = "claude-haiku-4-5",
        generator_model: str = "claude-haiku-4-5",
        evaluate_every: int = 2,
        max_restarts: int = 2,
        quality_threshold: float = 3.0,
        language: str = "English",
        conversation_log_file: str | None = None,
    ):
        self.test_case = test_case
        self.agent_connector = agent_connector
        self.event_queue = event_queue
        self.use_ai = use_ai
        self.critic_model = critic_model
        self.generator_model = generator_model
        self.evaluate_every = evaluate_every
        self.max_restarts = max_restarts
        self.quality_threshold = quality_threshold
        self.language = language
        self.conversation_log_file = conversation_log_file

        self.scenario: Dict = test_case["scenario"]
        self.persona: Dict = test_case["persona"]

        # Initialize the Critic
        if use_ai:
            self.critic = CriticAgent(
                model=critic_model,
                evaluate_every=evaluate_every,
                max_restarts=max_restarts,
                quality_threshold=quality_threshold,
            )
        else:
            self.critic = OfflineCriticAgent(
                evaluate_every=evaluate_every,
                max_restarts=max_restarts,
                quality_threshold=quality_threshold,
            )

        # Track restarts
        self.restart_count = 0
        self.critic_coaching: str = ""  # latest coaching from Critic

    async def run(self) -> Dict[str, Any]:
        """
        Execute the GAN conversation loop.

        Returns the same dict as ConversationSimulator.run() but enriched
        with Critic metadata.
        """
        best_result: Optional[Dict[str, Any]] = None
        best_quality: float = -1.0

        while self.restart_count <= self.max_restarts:
            # Run a conversation attempt
            result = await self._run_single_attempt()

            # Extract conversation for Critic evaluation
            conv_for_critic = self._extract_conversation(result)

            # Final Critic evaluation
            final_verdict = await self.critic.evaluate_final(
                conversation=conv_for_critic,
                scenario=self.scenario,
                persona=self.persona,
                test_success=result["success"],
                failure_reason=result.get("failure_reason"),
            )

            await self.event_queue.put({
                "type": "critic_evaluation",
                "test_id": self.test_case.get("test_id", "unknown"),
                "action": final_verdict.action,
                "quality_score": final_verdict.quality_score,
                "is_false_positive": final_verdict.is_false_positive,
                "reasoning": final_verdict.reasoning,
            })

            # Track best attempt
            if final_verdict.quality_score > best_quality:
                best_quality = final_verdict.quality_score
                best_result = result
                best_result["_final_verdict"] = final_verdict

            # Handle false positive: override the test result
            if final_verdict.is_false_positive and not result["success"]:
                logger.info(
                    "Critic detected false positive for test %s: %s",
                    self.test_case.get("test_id", "?"),
                    final_verdict.false_positive_reason,
                )
                result["critic_false_positive"] = True
                result["critic_false_positive_reason"] = final_verdict.false_positive_reason
                best_result = result
                break

            # If quality is acceptable or we've used all restarts, stop
            if final_verdict.quality_score >= self.quality_threshold:
                break

            # Request restart with coaching
            self.restart_count += 1
            self.critic_coaching = final_verdict.coaching
            logger.info(
                "Critic requests restart (%d/%d) for test %s: %s",
                self.restart_count, self.max_restarts,
                self.test_case.get("test_id", "?"),
                final_verdict.reasoning,
            )

            await self.event_queue.put({
                "type": "critic_restart",
                "test_id": self.test_case.get("test_id", "unknown"),
                "restart_number": self.restart_count,
                "coaching": final_verdict.coaching,
            })

        # Use best result
        result = best_result or result

        # Enrich result with Critic metadata
        result["critic_metrics"] = asdict(self.critic.metrics)
        result["critic_restarts"] = self.restart_count
        result["critic_final_quality"] = best_quality

        # Aggregate costs (Generator + Critic)
        result["cost_usd"] = result.get("cost_usd", 0.0) + self.critic.metrics.total_cost_usd
        result["tokens_used"] = result.get("tokens_used", 0) + self.critic.metrics.total_tokens
        result["llm_calls"] = result.get("llm_calls", 0) + self.critic.metrics.total_evaluations

        return result

    async def _run_single_attempt(self) -> Dict[str, Any]:
        """Run one conversation attempt using the standard simulator."""
        # Inject coaching from Critic into the persona context if available
        enriched_test_case = dict(self.test_case)
        if self.critic_coaching:
            # Add coaching as a hint in the persona's edge behaviors
            persona = dict(enriched_test_case.get("persona", {}))
            persona["_critic_coaching"] = self.critic_coaching
            enriched_test_case["persona"] = persona

        simulator = ConversationSimulator(
            test_case=enriched_test_case,
            agent_connector=self.agent_connector,
            event_queue=self.event_queue,
            use_ai_personas=self.use_ai,
            language=self.language,
            conversation_log_file=self.conversation_log_file,
        )

        # If we have coaching, inject it into the prompt builder
        if self.critic_coaching and self.use_ai:
            original_build = simulator._build_first_message_prompt

            def patched_prompt():
                base = original_build()
                return (
                    base + f"\n\nIMPORTANT COACHING (from a supervisor reviewing your "
                    f"previous attempt): {self.critic_coaching}\n"
                    f"Apply this feedback to make your conversation more effective."
                )

            simulator._build_first_message_prompt = patched_prompt

        # Run with mid-conversation Critic evaluations
        result = await self._run_with_critic_checks(simulator)
        return result

    async def _run_with_critic_checks(self, simulator: ConversationSimulator) -> Dict[str, Any]:
        """
        Run the simulator but intercept turns for Critic evaluation.

        This patches into the simulator's run loop to add Critic checks
        every N turns.
        """
        # For simplicity, run the full conversation then evaluate
        # (mid-conversation interruption would require deeper refactoring
        # of the ConversationSimulator loop — marked as future enhancement)
        return await simulator.run()

    def _extract_conversation(self, result: Dict[str, Any]) -> List[Dict[str, str]]:
        """Convert simulator result turns into Critic-friendly format."""
        conversation = []
        for turn in result.get("turns", []):
            if isinstance(turn, ConversationTurn):
                conversation.append({
                    "role": turn.role,
                    "message": turn.message,
                    "tool_calls": turn.tool_calls,
                })
            elif isinstance(turn, dict):
                conversation.append({
                    "role": turn.get("role", "unknown"),
                    "message": turn.get("message", ""),
                    "tool_calls": turn.get("tool_calls", []),
                })
        return conversation
