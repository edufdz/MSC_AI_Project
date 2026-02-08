"""
TestExecutionEngine: orchestrates parallel execution of the full test suite.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .agent_connector import AgentConnector
from .conversation_simulator import ConversationSimulator
from .models import TestResult, TestStatus


class TestExecutionEngine:
    """
    Runs all test cases in parallel (bounded by ``max_workers``),
    emits events for the live monitor, and collects results.
    """

    def __init__(
        self,
        test_suite: Dict[str, Any],
        agent_connector: AgentConnector,
        max_workers: int = 10,
        use_ai_personas: bool = True,
        traces_dir: str | None = None,
        language: str = "English",
        conversation_log_file: str | None = None,
        agent_map: Dict[str, Any] | None = None,
    ):
        self.test_suite = test_suite
        self.agent_connector = agent_connector
        self.max_workers = max_workers
        self.use_ai_personas = use_ai_personas
        self.traces_dir = traces_dir
        self.language = language
        self.conversation_log_file = conversation_log_file

        # Extract goal-driven config from agent_map (terminal_outcomes, tool_chains, etc.)
        self._agent_map_extras: Dict[str, Any] = {}
        if agent_map:
            for key in ("terminal_outcomes", "tool_chains", "confirmation_phrases"):
                if key in agent_map:
                    self._agent_map_extras[key] = agent_map[key]

        self.test_cases: List[Dict] = test_suite.get("test_cases", [])
        self.results: List[TestResult] = []

        # Shared event queue consumed by the monitor
        self.event_queue: asyncio.Queue = asyncio.Queue()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def run_all(self) -> List[TestResult]:
        """Execute every test case and return the collected results."""
        await self._emit({
            "type": "run_started",
            "total_tests": len(self.test_cases),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        semaphore = asyncio.Semaphore(self.max_workers)

        tasks = [
            self._run_single(tc, semaphore)
            for tc in self.test_cases
        ]

        raw = await asyncio.gather(*tasks, return_exceptions=True)

        self.results = [r for r in raw if isinstance(r, TestResult)]

        # Log any unexpected exceptions
        for r in raw:
            if isinstance(r, Exception):
                await self._emit({
                    "type": "internal_error",
                    "error": str(r),
                })

        await self._emit({
            "type": "run_completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return self.results

    # ------------------------------------------------------------------
    # Single test execution
    # ------------------------------------------------------------------

    async def _run_single(
        self,
        test_case: Dict[str, Any],
        semaphore: asyncio.Semaphore,
    ) -> TestResult:
        async with semaphore:
            test_id = test_case.get("test_id", str(uuid.uuid4()))
            test_number = test_case.get("test_number", 0)
            started_at = datetime.now(timezone.utc)

            result = TestResult(
                test_id=test_id,
                test_number=test_number,
                status=TestStatus.RUNNING,
                scenario_title=test_case.get("scenario", {}).get("title", ""),
                persona_name=test_case.get("persona", {}).get("name", ""),
                difficulty=test_case.get("difficulty", "medium"),
                coverage_goal=test_case.get("coverage_goal", ""),
                started_at=started_at,
            )

            await self._emit({
                "type": "test_started",
                "test_id": test_id,
                "test_number": test_number,
                "scenario": result.scenario_title,
                "persona": result.persona_name,
            })

            try:
                timeout_sec = test_case.get("execution_config", {}).get(
                    "timeout_per_tool_call_sec", 10
                ) * test_case.get("scenario", {}).get("estimated_turns", 5) + 30

                conv_result = await asyncio.wait_for(
                    self._run_conversation(test_case),
                    timeout=timeout_sec,
                )

                result.status = TestStatus.PASSED if conv_result["success"] else TestStatus.FAILED
                result.success = conv_result["success"]
                result.failure_reason = conv_result.get("failure_reason")
                result.outcome = conv_result.get("outcome")
                result.tools_called_sequence = conv_result.get("tools_called_sequence", [])
                result.tool_results = conv_result.get("tool_results", [])
                result.turns = conv_result["turns"]
                result.total_turns = len(conv_result["turns"])
                result.chaos_events = conv_result.get("chaos_events", [])
                result.llm_calls = conv_result["llm_calls"]
                result.tool_calls_count = conv_result["tool_calls_count"]
                result.tokens_used = conv_result["tokens_used"]
                result.cost_usd = conv_result["cost_usd"]

            except asyncio.TimeoutError:
                result.status = TestStatus.TIMEOUT
                result.failure_reason = "Test exceeded maximum duration"

            except Exception as e:
                result.status = TestStatus.ERROR
                result.failure_reason = f"Unexpected error: {e}"

            result.completed_at = datetime.now(timezone.utc)
            result.duration_sec = (result.completed_at - result.started_at).total_seconds()

            # Save trace
            if self.traces_dir:
                trace_path = self._save_trace(result)
                result.trace_file = trace_path

            await self._emit({
                "type": "test_completed",
                "test_id": test_id,
                "test_number": test_number,
                "status": result.status.value,
                "success": result.success,
                "duration_sec": result.duration_sec,
                "cost_usd": result.cost_usd,
                "scenario": result.scenario_title,
                "persona": result.persona_name,
                "failure_reason": result.failure_reason,
            })

            return result

    async def _run_conversation(self, test_case: Dict) -> Dict[str, Any]:
        # Inject agent_map extras (terminal_outcomes, tool_chains) into test_case
        enriched = dict(test_case)
        if self._agent_map_extras:
            enriched.setdefault("agent_map", {}).update(self._agent_map_extras)

        simulator = ConversationSimulator(
            test_case=enriched,
            agent_connector=self.agent_connector,
            event_queue=self.event_queue,
            use_ai_personas=self.use_ai_personas,
            language=self.language,
            conversation_log_file=self.conversation_log_file,
        )
        return await simulator.run()

    # ------------------------------------------------------------------
    # Trace persistence
    # ------------------------------------------------------------------

    def _save_trace(self, result: TestResult) -> str:
        traces = Path(self.traces_dir)
        traces.mkdir(parents=True, exist_ok=True)
        filename = f"trace_{result.test_number:04d}_{result.test_id[:8]}.json"
        filepath = traces / filename

        trace_data = result.model_dump()
        with open(filepath, "w") as f:
            json.dump(trace_data, f, indent=2, default=str)

        return str(filepath)

    # ------------------------------------------------------------------
    # Event helpers
    # ------------------------------------------------------------------

    async def _emit(self, event: Dict[str, Any]) -> None:
        await self.event_queue.put(event)
