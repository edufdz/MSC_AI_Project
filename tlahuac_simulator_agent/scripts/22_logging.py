#!/usr/bin/env python3
"""
Step 5.2: Logging + Traces
Log every simulated turn for debugging and reproducibility
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

# Runs directory
RUNS_DIR = Path(__file__).parent.parent / "runs"


def init_run_log(run_id: str, scenario: str, persona: str, seed: int) -> Path:
    """
    Initialize a new run log file.
    
    Args:
        run_id: Unique run identifier (e.g., "run_20260128_001")
        scenario: Scenario name
        persona: Persona name
        seed: Random seed for reproducibility
    
    Returns:
        Path to log file
    """
    # Create runs directory if it doesn't exist
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create log file
    log_file = RUNS_DIR / f"{run_id}.jsonl"
    
    # Write initial metadata
    metadata = {
        "run_id": run_id,
        "scenario": scenario,
        "persona": persona,
        "seed": seed,
        "started_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "turns": []
    }
    
    # Log file will be written line by line, but we can write metadata comment
    with open(log_file, 'w', encoding='utf-8') as f:
        # Write metadata as first line (JSON comment format)
        f.write(f"# METADATA: {json.dumps(metadata, ensure_ascii=False)}\n")
    
    return log_file


def log_turn(run_id: str, turn_data: Dict) -> None:
    """
    Log a single turn to the run log file.
    
    Args:
        run_id: Run identifier
        turn_data: Dict with turn information (see plan for structure)
    """
    log_file = RUNS_DIR / f"{run_id}.jsonl"
    
    if not log_file.exists():
        raise FileNotFoundError(f"Run log not initialized: {log_file}")
    
    # Append turn as JSON line
    with open(log_file, 'a', encoding='utf-8') as f:
        json_line = json.dumps(turn_data, ensure_ascii=False)
        f.write(json_line + '\n')


def finalize_run(run_id: str, final_state: Dict) -> None:
    """
    Finalize run log with summary statistics.
    
    Args:
        run_id: Run identifier
        final_state: Final conversation state
    """
    log_file = RUNS_DIR / f"{run_id}.jsonl"
    
    if not log_file.exists():
        return
    
    # Read all turns
    turns = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                continue
            if not line:
                continue
            try:
                turn = json.loads(line)
                turns.append(turn)
            except json.JSONDecodeError:
                continue
    
    # Calculate statistics
    total_turns = len(turns)
    customer_turns = sum(1 for t in turns if t.get('role') == 'customer')
    total_cost = sum(t.get('metadata', {}).get('cost_usd', 0) for t in turns)
    total_latency = sum(t.get('metadata', {}).get('latency_ms', 0) for t in turns)
    
    # Write summary
    summary = {
        "run_id": run_id,
        "ended_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_turns": total_turns,
        "customer_turns": customer_turns,
        "total_cost_usd": total_cost,
        "total_latency_ms": total_latency,
        "avg_latency_ms": total_latency / total_turns if total_turns > 0 else 0,
        "final_state": final_state
    }
    
    # Append summary
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"# SUMMARY: {json.dumps(summary, ensure_ascii=False)}\n")
    
    # Update run metadata file
    metadata_file = RUNS_DIR / "run_metadata.json"
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            all_runs = json.load(f)
    else:
        all_runs = {"runs": []}
    
    all_runs["runs"].append({
        "run_id": run_id,
        "scenario": final_state.get('scenario'),
        "persona": final_state.get('persona'),
        "started_at": turns[0].get('timestamp') if turns else None,
        "ended_at": summary["ended_at"],
        "total_turns": total_turns,
        "total_cost_usd": total_cost
    })
    
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(all_runs, f, ensure_ascii=False, indent=2)


def load_run(run_id: str) -> Dict:
    """
    Load a run from log file.
    
    Args:
        run_id: Run identifier
    
    Returns:
        Dict with run data
    """
    log_file = RUNS_DIR / f"{run_id}.jsonl"
    
    if not log_file.exists():
        raise FileNotFoundError(f"Run log not found: {log_file}")
    
    metadata = None
    turns = []
    summary = None
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('# METADATA:'):
                metadata_json = line.replace('# METADATA: ', '')
                metadata = json.loads(metadata_json)
            elif line.startswith('# SUMMARY:'):
                summary_json = line.replace('# SUMMARY: ', '')
                summary = json.loads(summary_json)
            elif line and not line.startswith('#'):
                try:
                    turn = json.loads(line)
                    turns.append(turn)
                except json.JSONDecodeError:
                    continue
    
    return {
        "metadata": metadata,
        "turns": turns,
        "summary": summary
    }


def main():
    """Test logging functions."""
    # Test initialization
    run_id = "test_run_001"
    log_file = init_run_log(run_id, "booking_service_appointment", "calm_cooperative", 12345)
    print(f"Created log file: {log_file}")
    
    # Test logging a turn
    turn_data = {
        "run_id": run_id,
        "turn_idx": 0,
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "role": "customer",
        "inputs": {
            "dealership_message": "¿Cómo podemos ayudarte?",
            "scenario": "booking_service_appointment",
            "stage": "opening",
            "persona": "calm_cooperative"
        },
        "output": {
            "customer_message": "Hola, quiero agendar una cita"
        },
        "filters": {
            "was_filtered": False,
            "content_valid": True
        },
        "metadata": {
            "cost_usd": 0.0001,
            "latency_ms": 450
        }
    }
    
    log_turn(run_id, turn_data)
    print("Logged turn")
    
    # Test finalization
    final_state = {
        "scenario": "booking_service_appointment",
        "persona": "calm_cooperative",
        "turn_count": 1
    }
    finalize_run(run_id, final_state)
    print("Finalized run")
    
    # Test loading
    loaded = load_run(run_id)
    print(f"Loaded run: {len(loaded['turns'])} turns")


if __name__ == "__main__":
    main()
