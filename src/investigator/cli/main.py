"""Command Line Interface for AI Software Investigator.

Provides subcommands for case intake, hypothesis management, experiment execution,
black-box boundary searching, statistical verification, and live demos.
"""

from pathlib import Path
from typing import Optional
import argparse
import sys

from rich.console import Console

from investigator.cli.ui import (
    print_banner,
    print_confidence_card,
    print_status_board,
)
from investigator.engine.investigator import InvestigationEngine
from investigator.engine.protocol import CaseCategory, InvestigationVerdict
from investigator.engine.state import InvestigationState
from investigator.experiments.blackbox import BlackboxInvestigator

console = Console()


def cmd_new(args: argparse.Namespace) -> None:
    """Initialize a new investigation case."""
    target_dir = Path(args.dir).resolve()
    engine = InvestigationEngine(project_dir=target_dir, use_sandbox=not args.no_sandbox)
    case_id = args.case_id or f"CASE-{datetime_stamp()}"

    case = engine.intake(
        case_id=case_id,
        title=args.title,
        problem_statement=args.problem,
        category=CaseCategory(args.category),
    )
    engine.discover_environment()

    print_banner(case.case_id)
    console.print(f"[bold green]✓ Initialized investigation case in:[/bold green] {target_dir}")
    console.print(f"[bold cyan]Case ID:[/bold cyan] {case.case_id}")
    console.print(f"[bold]Title:[/bold] {case.title}\n")
    print_status_board(engine.state)


def cmd_status(args: argparse.Namespace) -> None:
    """Display the current forensic status board."""
    target_dir = Path(args.dir).resolve()
    state = InvestigationState(target_dir)
    print_status_board(state)


def cmd_blackbox(args: argparse.Namespace) -> None:
    """Run automated black-box boundary discovery on a command."""
    print_banner()
    console.print(f"[bold yellow]Initiating Black-box Investigation on:[/bold yellow] `{args.cmd}`\n")

    investigator = BlackboxInvestigator()
    console.print(f"Executing binary search on input length parameter ({args.min_len} .. {args.max_len})...")
    result = investigator.binary_search_length_boundary(
        command_template=args.cmd,
        min_len=args.min_len,
        max_len=args.max_len,
        use_stdin=args.use_stdin,
        char=args.char,
    )

    if result:
        console.print("\n[bold green]✓ EXACT FAILURE BOUNDARY ISOLATED![/bold green]")
        console.print(f"[bold]Passing Bound (OK):[/bold]    Length {result.lower_passing_bound}")
        console.print(f"[bold]Failing Bound (CRASH):[/bold] Length {result.upper_failing_bound}")
        console.print(f"\n[italic]{result.trigger_description}[/italic]\n")

        console.print("[bold cyan]Search Steps:[/bold cyan]")
        for step in result.search_history:
            status_style = "green" if step['status'] == "pass" else "bold red"
            console.print(f"  - Length {step['length']:4d} -> Exit {step['exit_code']} [{status_style}]{step['status'].upper()}[/{status_style}]")
    else:
        console.print("[bold red]No failure transition found in the given length range.[/bold red]")


def cmd_demo(args: argparse.Namespace) -> None:
    """Run an automated forensic demonstration."""
    import sys
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    if str(Path.cwd()) not in sys.path:
        sys.path.insert(0, str(Path.cwd()))

    demo_num = args.number
    if demo_num == 1:
        from examples.demo_01_logic import run_demo_01
        run_demo_01()
    elif demo_num == 2:
        from examples.demo_02_race import run_demo_02
        run_demo_02()
    elif demo_num == 3:
        from examples.demo_03_blackbox import run_demo_03
        run_demo_03()
    else:
        console.print(f"[bold red]Unknown demo number: {demo_num}. Available: 1, 2, 3.[/bold red]")


def cmd_auto(args: argparse.Namespace) -> None:
    """Run autonomous investigation loop driven by AI reasoning."""
    target_dir = Path(args.dir).resolve()
    from investigator.agent.core import AutonomousInvestigator
    from investigator.agent.llm import (
        HeuristicForensicDriver,
        LLMReasoningProvider,
        DeepSeekReasoningProvider,
        DoubaoReasoningProvider,
    )

    provider_type = getattr(args, "provider", "heuristic")
    if getattr(args, "use_llm", False) and provider_type == "heuristic":
        provider_type = "openai"

    if provider_type == "deepseek":
        provider = DeepSeekReasoningProvider(model=args.model or "deepseek-reasoner")
    elif provider_type == "doubao":
        provider = DoubaoReasoningProvider(model=args.model or "doubao-1.5-pro-32k")
    elif provider_type == "openai":
        provider = LLMReasoningProvider(model=args.model or "gpt-4o")
    else:
        provider = HeuristicForensicDriver()

    agent = AutonomousInvestigator(
        project_dir=target_dir,
        provider=provider,
        use_sandbox=not args.no_sandbox,
    )

    agent.investigate(
        problem_statement=args.problem,
        title=args.title,
        category=CaseCategory(args.category),
        repro_command=args.repro,
        max_steps=args.max_steps,
    )


def cmd_harness(args: argparse.Namespace) -> None:
    """Run investigation via DeepSeek / SWE-bench evaluation harness."""
    from investigator.harness.deepseek import DeepSeekHarness, HarnessTaskSpec
    import json

    harness = DeepSeekHarness(
        use_deepseek_api=getattr(args, "use_deepseek", False),
        deepseek_model=getattr(args, "model", "deepseek-reasoner"),
    )

    if args.spec:
        spec_path = Path(args.spec).resolve()
        with open(spec_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            specs = [HarnessTaskSpec.from_dict(d, base_dir=spec_path.parent) for d in data]
            results = harness.run_suite(specs)
            out_data = [r.to_dict() for r in results]
        else:
            spec = HarnessTaskSpec.from_dict(data, base_dir=spec_path.parent)
            res = harness.run_task(spec)
            out_data = res.to_dict()
    else:
        spec = HarnessTaskSpec(
            instance_id=args.instance_id or f"HARNESS-{datetime_stamp()}",
            problem_statement=args.problem or "Automatic Harness Problem",
            repo_dir=Path(args.dir).resolve(),
            test_command=args.test_cmd,
            category=args.category,
            max_steps=args.max_steps,
        )
        res = harness.run_task(spec)
        out_data = res.to_dict()

    if args.output:
        out_path = Path(args.output).resolve()
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out_data, f, indent=2)
        console.print(f"[bold green]✓ Harness evaluation results saved to:[/bold green] {out_path}")
    else:
        console.print(f"\n[bold cyan]Harness Evaluation Result:[/bold cyan]")
        console.print(json.dumps(out_data, indent=2))


def datetime_stamp() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="investigator",
        description="AI Software Investigator: Autonomous Forensic Investigation Engine"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # auto (Autonomous AI Investigation)
    p_auto = subparsers.add_parser("auto", help="Launch autonomous AI investigation loop")
    p_auto.add_argument("--dir", default=".", help="Target project directory")
    p_auto.add_argument("--problem", required=True, help="Problem statement or bug report")
    p_auto.add_argument("--title", default="Autonomous Investigation", help="Case title")
    p_auto.add_argument("--repro", help="Optional baseline reproduction command")
    p_auto.add_argument(
        "--category",
        default="bug",
        choices=["bug", "performance", "reliability", "behavioral", "blackbox"],
        help="Investigation category"
    )
    p_auto.add_argument("--max-steps", type=int, default=15, help="Maximum reasoning loop steps")
    p_auto.add_argument(
        "--provider",
        default="heuristic",
        choices=["heuristic", "openai", "deepseek", "doubao"],
        help="Reasoning provider backend (heuristic offline driver, openai, deepseek, or doubao)"
    )
    p_auto.add_argument("--use-llm", action="store_true", help="Use live LLM API (OpenAI/Anthropic) instead of offline forensic driver")
    p_auto.add_argument("--model", default=None, help="LLM model name (e.g. deepseek-reasoner, doubao-1.5-pro-32k, gpt-4o)")

    # harness (DeepSeek & Automated Benchmark Harness)
    p_harness = subparsers.add_parser("harness", help="Run DeepSeek / benchmark evaluation harness")
    p_harness.add_argument("--spec", help="Path to JSON task spec file or suite list")
    p_harness.add_argument("--dir", default=".", help="Target project directory")
    p_harness.add_argument("--problem", help="Problem statement")
    p_harness.add_argument("--test-cmd", help="Verification test command")
    p_harness.add_argument("--instance-id", help="Benchmark instance ID")
    p_harness.add_argument("--category", default="bug", help="Task category")
    p_harness.add_argument("--max-steps", type=int, default=15, help="Max reasoning steps")
    p_harness.add_argument("--use-deepseek", action="store_true", help="Use live DeepSeek reasoning API")
    p_harness.add_argument("--model", default="deepseek-reasoner", help="DeepSeek model (deepseek-reasoner or deepseek-chat)")
    p_harness.add_argument("--output", "-o", help="Output path for JSON results")

    # new
    p_new = subparsers.add_parser("new", help="Initialize a new investigation case")
    p_new.add_argument("--dir", default=".", help="Target project directory")
    p_new.add_argument("--case-id", help="Explicit Case ID (e.g. CASE-2026-0001)")
    p_new.add_argument("--title", required=True, help="Investigation title")
    p_new.add_argument("--problem", required=True, help="Problem statement")
    p_new.add_argument(
        "--category",
        default="bug",
        choices=["bug", "performance", "reliability", "behavioral", "blackbox"],
        help="Investigation category"
    )
    p_new.add_argument("--no-sandbox", action="store_true", help="Disable filesystem sandbox")

    # status
    p_status = subparsers.add_parser("status", help="Show current investigation dashboard")
    p_status.add_argument("--dir", default=".", help="Target project directory")

    # blackbox
    p_bb = subparsers.add_parser("blackbox", help="Run automated black-box boundary search")
    p_bb.add_argument("--cmd", required=True, help="Command template with {input} placeholder")
    p_bb.add_argument("--min-len", type=int, default=1, help="Minimum search length")
    p_bb.add_argument("--max-len", type=int, default=512, help="Maximum search length")
    p_bb.add_argument("--char", default="A", help="Character to repeat")
    p_bb.add_argument("--use-stdin", action="store_true", help="Pass payload via stdin")

    # demo
    p_demo = subparsers.add_parser("demo", help="Run end-to-end forensic demonstration")
    p_demo.add_argument("number", type=int, choices=[1, 2, 3], help="Demo number (1: Logic Bug, 2: Intermittent Race, 3: Black-box Boundary)")

    args = parser.parse_args()
    if not args.subcommand:
        parser.print_help()
        sys.exit(0)

    if args.subcommand == "auto":
        cmd_auto(args)
    elif args.subcommand == "harness":
        cmd_harness(args)
    elif args.subcommand == "new":
        cmd_new(args)
    elif args.subcommand == "status":
        cmd_status(args)
    elif args.subcommand == "blackbox":
        cmd_blackbox(args)
    elif args.subcommand == "demo":
        cmd_demo(args)


if __name__ == "__main__":
    main()
