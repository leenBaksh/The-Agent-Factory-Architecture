#!/usr/bin/env python3
"""
Agent Evals Runner for Digital FTEs

Runs the Golden Dataset scenarios against a Digital FTE and calculates
accuracy scores. This is the "exam" that every Digital FTE must pass
before deployment.

Usage:
    python evals/run_evals.py --min-accuracy 0.95
    python evals/run_evals.py --scenario-dir evals/invoice-processor
    python evals/run_evals.py --output results.json
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def load_golden_dataset(dataset_path: str) -> list[dict]:
    """Load and parse the golden dataset YAML file."""
    with open(dataset_path, "r") as f:
        data = yaml.safe_load(f)
    return data.get("scenarios", [])


def run_single_scenario(scenario: dict, fte_endpoint: str) -> dict:
    """
    Run a single scenario against the Digital FTE.

    In production, this would:
    1. Send the scenario input to the FTE via API
    2. Capture the FTE's response
    3. Compare against expected output

    For now, this is a placeholder that simulates the evaluation.
    """
    scenario_id = scenario["id"]
    description = scenario["description"]
    expected = scenario["expected"]

    # TODO: Replace with actual FTE API call
    # response = requests.post(f"{fte_endpoint}/tasks", json={"task": scenario["input"]})
    # actual = response.json()

    # Simulated result (replace with actual FTE response)
    result = {
        "scenario_id": scenario_id,
        "description": description,
        "status": "simulated",
        "expected": expected,
        "actual": None,  # Would be populated from FTE response
        "passed": False,
        "score": 0.0,
        "details": "Simulation mode - connect to actual FTE for real evals",
    }

    return result


def calculate_accuracy(results: list[dict]) -> dict:
    """Calculate overall accuracy and per-category scores."""
    total = len(results)
    passed = sum(1 for r in results if r.get("passed", False))
    avg_score = sum(r.get("score", 0) for r in results) / total if total > 0 else 0

    return {
        "total_scenarios": total,
        "passed": passed,
        "failed": total - passed,
        "accuracy": passed / total if total > 0 else 0,
        "average_score": avg_score,
        "timestamp": datetime.utcnow().isoformat(),
    }


def generate_report(accuracy: dict, results: list[dict], output_path: str):
    """Generate a human-readable evaluation report."""
    report = {
        "summary": accuracy,
        "results": results,
        "recommendations": [],
    }

    # Add recommendations based on accuracy
    if accuracy["accuracy"] >= 0.95:
        report["recommendations"].append(
            "✅ FTE meets production threshold (95%+). Ready for deployment."
        )
    elif accuracy["accuracy"] >= 0.90:
        report["recommendations"].append(
            "⚠️ FTE is close to production threshold. Review failed scenarios and improve."
        )
    else:
        report["recommendations"].append(
            "❌ FTE does not meet production threshold. Significant improvements needed."
        )

    # List failed scenarios
    failed = [r for r in results if not r.get("passed", False)]
    if failed:
        report["failed_scenarios"] = [
            {"id": r["scenario_id"], "description": r["description"]} for r in failed
        ]

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    return report


def main():
    parser = argparse.ArgumentParser(description="Run Agent Evals (Golden Dataset)")
    parser.add_argument(
        "--scenario-dir",
        default="evals/invoice-processor",
        help="Directory containing golden_dataset.yaml",
    )
    parser.add_argument(
        "--min-accuracy",
        type=float,
        default=0.95,
        help="Minimum accuracy threshold (default: 0.95)",
    )
    parser.add_argument(
        "--fte-endpoint",
        default="http://localhost:8000",
        help="Digital FTE API endpoint",
    )
    parser.add_argument(
        "--output",
        default="evals/results.json",
        help="Output file for results",
    )

    args = parser.parse_args()

    # Load golden dataset
    dataset_path = os.path.join(args.scenario_dir, "golden_dataset.yaml")
    if not os.path.exists(dataset_path):
        print(f"❌ Golden dataset not found: {dataset_path}")
        sys.exit(1)

    scenarios = load_golden_dataset(dataset_path)
    print(f"📋 Loaded {len(scenarios)} scenarios from {dataset_path}")

    # Run evaluations
    print("\n🧪 Running evaluations...")
    results = []
    start_time = time.time()

    for i, scenario in enumerate(scenarios, 1):
        print(f"  [{i}/{len(scenarios)}] {scenario['id']}: {scenario['description']}")
        result = run_single_scenario(scenario, args.fte_endpoint)
        results.append(result)

    elapsed = time.time() - start_time
    print(f"\n⏱️  Completed in {elapsed:.2f} seconds")

    # Calculate accuracy
    accuracy = calculate_accuracy(results)
    print(f"\n📊 Results:")
    print(f"   Total: {accuracy['total_scenarios']}")
    print(f"   Passed: {accuracy['passed']}")
    print(f"   Failed: {accuracy['failed']}")
    print(f"   Accuracy: {accuracy['accuracy']:.1%}")
    print(f"   Avg Score: {accuracy['average_score']:.2f}")

    # Generate report
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    report = generate_report(accuracy, results, args.output)
    print(f"\n📄 Report saved to: {args.output}")

    # Check threshold
    if accuracy["accuracy"] >= args.min_accuracy:
        print(f"\n✅ PASSED: Accuracy {accuracy['accuracy']:.1%} >= {args.min_accuracy:.1%}")
        sys.exit(0)
    else:
        print(f"\n❌ FAILED: Accuracy {accuracy['accuracy']:.1%} < {args.min_accuracy:.1%}")
        sys.exit(1)


if __name__ == "__main__":
    main()
