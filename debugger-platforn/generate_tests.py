#!/usr/bin/env python3
"""
Test Generation CLI (Unified Phase B)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Single entry point that runs B1→B2→B3→B4 in sequence:
  1. Coverage goals & sandbox config  (coverage_builder)
  2. Persona library                  (persona_builder)
  3. Scenario catalog                 (scenario_builder)
  4. Test suite generation            (testsuite_builder)

Usage:
    # Offline (no API key needed)
    python generate_tests.py agent_map.json --skip-ai --count 20

    # With AI enrichment
    python generate_tests.py agent_map.json --count 250 --persona-count 8 --scenario-count 10

    # Custom output directory
    python generate_tests.py agent_map.json --skip-ai --output-dir my_tests/
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Load .env and set up path
project_root = Path(__file__).parent
load_dotenv(project_root / ".env")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.coverage.calculator import build_test_configuration
from src.personas.builder import PersonaBuilder
from src.personas.models import PersonaLibrary
from src.scenarios.library import ScenarioLibrary
from src.scenarios.models import ScenarioCatalog
from src.coverage.models import TestConfiguration
from src.generator.test_suite import TestSuiteGenerator

console = Console()


def _run_phase_b(
    agent_map: dict,
    output_dir: Path,
    skip_ai: bool,
    count: int,
    persona_count: int,
    scenario_count: int,
    variants: int,
    seed: int | None,
    language: str | None,
) -> str:
    """Run all four Phase B sub-steps. Returns path to test_suite.json."""
    import random as _random
    if seed is not None:
        _random.seed(seed)

    output_dir.mkdir(parents=True, exist_ok=True)
    has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY"))

    # ── B3: Coverage goals & sandbox config ──
    console.print(Panel(
        "[bold]Step 1/4: Coverage Configuration[/bold]\n"
        "Calculate coverage goals and sandbox config from agent map",
        style="blue",
    ))

    with console.status("[bold green]Building test configuration..."):
        config = build_test_configuration(agent_map)

    config_path = output_dir / "test_configuration.json"
    with open(config_path, "w") as f:
        json.dump(config.model_dump(), f, indent=2, default=str)

    tool_count = len(config.coverage_goals.tool_coverage.min_invocations_per_tool)
    combo_count = len(config.coverage_goals.tool_coverage.tool_combinations)
    console.print(
        f"  [green]Done[/green] — {tool_count} tools, "
        f"{combo_count} combos → [cyan]{config_path}[/cyan]"
    )

    # ── B1: Persona library ──
    console.print()
    console.print(Panel(
        "[bold]Step 2/4: Persona Library[/bold]\n"
        "Generate synthetic user personas for testing",
        style="blue",
    ))

    builder = PersonaBuilder(agent_map)
    with console.status("[bold green]Loading persona templates..."):
        builder.load_templates()

    # AI-generated personas
    if persona_count > 0 and not skip_ai and has_api_key:
        with console.status(f"[bold green]Generating {persona_count} AI personas..."):
            builder.generate_personas(count=persona_count)
        console.print(f"  Generated [green]{persona_count}[/green] AI personas")
    elif persona_count > 0 and (skip_ai or not has_api_key):
        reason = "--skip-ai" if skip_ai else "ANTHROPIC_API_KEY not set"
        console.print(f"  [yellow]AI persona generation skipped ({reason})[/yellow]")

    library = builder.export_library()
    persona_path = output_dir / "persona_library.json"
    with open(persona_path, "w") as f:
        json.dump(library.model_dump(), f, indent=2, default=str)

    console.print(
        f"  [green]Done[/green] — {len(builder.personas)} personas → [cyan]{persona_path}[/cyan]"
    )

    # ── B2: Scenario catalog ──
    console.print()
    console.print(Panel(
        "[bold]Step 3/4: Scenario Catalog[/bold]\n"
        "Create test scenarios for agent testing",
        style="blue",
    ))

    scenario_lib = ScenarioLibrary(agent_map)
    with console.status("[bold green]Loading scenario templates..."):
        scenario_lib.load_templates()

    # AI-generated scenarios
    if scenario_count > 0 and not skip_ai and has_api_key:
        with console.status(f"[bold green]Generating {scenario_count} AI scenarios..."):
            scenario_lib.generate_scenarios(count=scenario_count)
        console.print(f"  Generated [green]{scenario_count}[/green] AI scenarios")
    elif scenario_count > 0 and (skip_ai or not has_api_key):
        reason = "--skip-ai" if skip_ai else "ANTHROPIC_API_KEY not set"
        console.print(f"  [yellow]AI scenario generation skipped ({reason})[/yellow]")

    # Variant expansion
    if variants > 0:
        bases = [s for s in scenario_lib.scenarios if s.base_scenario_id is None]
        total_variants = 0
        if skip_ai or not has_api_key:
            for base in bases:
                v = scenario_lib.generate_offline_variants(base)
                total_variants += len(v)
        else:
            for base in bases:
                with console.status(f"[green]  Generating variants for {base.title}..."):
                    v = scenario_lib.generate_variants(base, count=variants)
                total_variants += len(v)
        console.print(f"  Variants generated: [green]{total_variants}[/green]")

    catalog = scenario_lib.export_catalog()
    scenario_path = output_dir / "scenario_catalog.json"
    with open(scenario_path, "w") as f:
        json.dump(catalog.model_dump(), f, indent=2, default=str)

    console.print(
        f"  [green]Done[/green] — {catalog.total_scenarios_count} scenarios → [cyan]{scenario_path}[/cyan]"
    )

    # ── B4: Test suite generation ──
    console.print()
    console.print(Panel(
        "[bold]Step 4/4: Test Suite Generation[/bold]\n"
        "Combine personas, scenarios, and coverage goals into executable tests",
        style="blue",
    ))

    with console.status(f"[bold green]Generating {count} test cases..."):
        generator = TestSuiteGenerator(
            agent_map=agent_map,
            personas=library.personas,
            scenarios=catalog.scenarios,
            coverage_goals=config.coverage_goals,
            sandbox_config=config.sandbox_config,
        )
        suite = generator.generate(target_count=count)

    suite_path = output_dir / "test_suite.json"
    with open(suite_path, "w") as f:
        json.dump(suite.model_dump(), f, indent=2, default=str)

    console.print(
        f"  [green]Done[/green] — {suite.summary.total_tests} test cases → [cyan]{suite_path}[/cyan]"
    )

    return str(suite_path)


@click.command()
@click.argument("agent_map_file", type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="generated", help="Output directory for all generated files")
@click.option("--skip-ai", is_flag=True, help="Skip all AI generation (offline mode)")
@click.option("--count", "-c", default=250, type=int, help="Target number of test cases (default 250)")
@click.option("--persona-count", default=8, type=int, help="Number of AI-generated personas (default 8)")
@click.option("--scenario-count", default=10, type=int, help="Number of AI-generated scenarios (default 10)")
@click.option("--variants", default=3, type=int, help="Variants per base scenario (default 3)")
@click.option("--seed", default=None, type=int, help="Random seed for reproducibility")
@click.option("--language", "-l", default=None, help="Language for generated content")
def main(
    agent_map_file: str,
    output_dir: str,
    skip_ai: bool,
    count: int,
    persona_count: int,
    scenario_count: int,
    variants: int,
    seed: int | None,
    language: str | None,
):
    """Run unified Phase B: generate test suite from agent map (B1→B2→B3→B4)."""
    start = time.time()

    console.print(Panel(
        "[bold]Phase B: Test Generation Pipeline[/bold]\n"
        "Coverage → Personas → Scenarios → Test Suite",
        style="blue",
    ))

    # Load agent map
    with open(agent_map_file) as f:
        agent_map = json.load(f)

    agent_type = agent_map.get("metadata", {}).get("type", "custom")
    console.print(f"  Agent type:    [cyan]{agent_type}[/cyan]")
    console.print(f"  Output dir:    [cyan]{output_dir}[/cyan]")
    console.print(f"  Target tests:  [bold]{count}[/bold]")
    console.print(f"  AI mode:       [bold]{'off' if skip_ai else 'on'}[/bold]")
    console.print()

    suite_path = _run_phase_b(
        agent_map=agent_map,
        output_dir=Path(output_dir),
        skip_ai=skip_ai,
        count=count,
        persona_count=persona_count,
        scenario_count=scenario_count,
        variants=variants,
        seed=seed,
        language=language,
    )

    elapsed = time.time() - start

    # Final summary
    console.print()
    console.print(Panel(
        f"  Test configuration: [cyan]{output_dir}/test_configuration.json[/cyan]\n"
        f"  Persona library:    [cyan]{output_dir}/persona_library.json[/cyan]\n"
        f"  Scenario catalog:   [cyan]{output_dir}/scenario_catalog.json[/cyan]\n"
        f"  Test suite:         [cyan]{suite_path}[/cyan]",
        title="[bold green]Phase B Complete[/bold green]",
        style="green",
    ))
    console.print(f"[dim]{elapsed:.1f}s[/dim]")


if __name__ == "__main__":
    main()
