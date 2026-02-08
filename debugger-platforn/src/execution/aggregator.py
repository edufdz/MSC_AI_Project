"""
ResultsAggregator: generates the final test-run report and failure inbox
from collected TestResult objects.
"""

from __future__ import annotations

import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .models import TestResult, TestRunReport


class ResultsAggregator:
    """Aggregate test results into a report + failure inbox."""

    def __init__(self, test_suite: Dict[str, Any], results: List[TestResult]):
        self.test_suite = test_suite
        self.results = results

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    def generate_report(self, started_at: datetime) -> TestRunReport:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status.value == "passed")
        failed = sum(1 for r in self.results if r.status.value == "failed")
        errors = sum(1 for r in self.results if r.status.value == "error")
        timeouts = sum(1 for r in self.results if r.status.value == "timeout")

        durations = [r.duration_sec for r in self.results]
        total_duration = sum(durations)
        avg_duration = total_duration / total if total else 0.0

        total_cost = sum(r.cost_usd for r in self.results)

        # Tool coverage
        tool_counts: Dict[str, int] = defaultdict(int)
        for r in self.results:
            for turn in r.turns:
                for tc in turn.tool_calls:
                    tool_counts[tc.get("tool_name", "unknown")] += 1

        expected_tools: List[str] = list(
            self.test_suite
            .get("summary", {})
            .get("tool_invocation_counts", {})
            .keys()
        )
        tools_not_covered = [t for t in expected_tools if t not in tool_counts]
        coverage_pct = (
            ((len(expected_tools) - len(tools_not_covered)) / len(expected_tools) * 100)
            if expected_tools else 0.0
        )

        # Breakdown by difficulty
        by_difficulty: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for r in self.results:
            by_difficulty[r.difficulty][r.status.value] += 1

        # Breakdown by coverage goal
        by_coverage: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for r in self.results:
            by_coverage[r.coverage_goal][r.status.value] += 1

        return TestRunReport(
            run_id=str(uuid.uuid4()),
            test_suite_id=self.test_suite.get("test_suite_id", "unknown"),
            total_tests=total,
            passed=passed,
            failed=failed,
            errors=errors,
            timeouts=timeouts,
            pass_rate=(passed / total * 100) if total else 0.0,
            total_duration_sec=total_duration,
            avg_duration_sec=avg_duration,
            total_cost_usd=total_cost,
            tool_coverage=dict(tool_counts),
            tools_not_covered=tools_not_covered,
            coverage_pct=coverage_pct,
            by_difficulty={k: dict(v) for k, v in by_difficulty.items()},
            by_coverage_goal={k: dict(v) for k, v in by_coverage.items()},
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------
    # Failure inbox (for Phase D)
    # ------------------------------------------------------------------

    def generate_failure_inbox(self) -> Dict[str, Any]:
        failures = [
            r for r in self.results
            if r.status.value in ("failed", "error", "timeout")
        ]

        return {
            "total_failures": len(failures),
            "by_status": {
                "failed": sum(1 for f in failures if f.status.value == "failed"),
                "error": sum(1 for f in failures if f.status.value == "error"),
                "timeout": sum(1 for f in failures if f.status.value == "timeout"),
            },
            "failures": [
                {
                    "test_id": f.test_id,
                    "test_number": f.test_number,
                    "scenario": f.scenario_title,
                    "persona": f.persona_name,
                    "difficulty": f.difficulty,
                    "coverage_goal": f.coverage_goal,
                    "status": f.status.value,
                    "failure_reason": f.failure_reason,
                    "total_turns": f.total_turns,
                    "duration_sec": f.duration_sec,
                    "cost_usd": f.cost_usd,
                    "chaos_events": [e.model_dump() for e in f.chaos_events],
                    "trace_file": f.trace_file,
                }
                for f in failures
            ],
        }

    # ------------------------------------------------------------------
    # Save helpers
    # ------------------------------------------------------------------

    def save_report(self, filepath: str | Path, started_at: datetime) -> TestRunReport:
        report = self.generate_report(started_at)
        with open(filepath, "w") as f:
            json.dump(report.model_dump(), f, indent=2, default=str)
        return report

    def save_failure_inbox(self, filepath: str | Path) -> Dict:
        inbox = self.generate_failure_inbox()
        with open(filepath, "w") as f:
            json.dump(inbox, f, indent=2, default=str)
        return inbox
