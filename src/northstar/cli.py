"""Command-line entry point for offline and hosted portfolio analysis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from northstar.contracts import ProgramScenario
from northstar.orchestrator import DecisionOrchestrator
from northstar.providers import ProviderError, build_provider


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Northstar Decision Lab")
    parser.add_argument("--scenario", type=Path, required=True, help="Path to a ProgramScenario JSON file")
    parser.add_argument("--output", type=Path, help="Optional report JSON output path")
    parser.add_argument("--provider", choices=("offline", "openai"), help="Override NORTHSTAR_PROVIDER")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        raw = json.loads(args.scenario.read_text(encoding="utf-8"))
        scenario = ProgramScenario.model_validate(raw)
        report = DecisionOrchestrator(provider=build_provider(args.provider)).run(scenario)
        rendered = report.model_dump_json(indent=None if args.compact else 2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        return 0
    except (OSError, json.JSONDecodeError, ValidationError, ProviderError) as exc:
        print(f"northstar: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
