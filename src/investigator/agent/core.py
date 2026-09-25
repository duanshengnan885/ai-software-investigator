"""Autonomous Investigation Agent Core for AI Software Investigator.

Drives the closed-loop autonomous reasoning cycle:
Observe State -> LLM/Reasoning Decision -> Tool Execution -> Update Ledger -> Next Step.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from investigator.agent.llm import BaseReasoningProvider, HeuristicForensicDriver, LLMReasoningProvider
from investigator.agent.tools import ForensicToolRegistry, ToolCall
from investigator.cli.ui import print_banner, print_status_board
from investigator.engine.investigator import InvestigationEngine
from investigator.engine.protocol import CaseCategory, InvestigationStage, InvestigationVerdict
from investigator.engine.termination import TerminationManager

console = Console()

FORENSIC_AGENT_SYSTEM_PROMPT = """You are AI Software Investigator (ASI), an autonomous forensic pathologist for software behavior.
Your mission is to systematically investigate, isolate, and verify software defects using the 12-Stage Forensic Protocol.

CORE MANDATE:
1. Evidence First: Never state a conclusion without an empirical evidence record.
2. Formulate falsifiable hypotheses with explicit mechanisms.
3. Plan experiments that maximize Information Gain to differentiate competing hypotheses.
4. Concurrency Sweep: For intermittent bugs, sweep concurrency (1 -> 4 -> 16 threads).
5. Minimal Fix: Make the smallest surgical modification that eliminates root cause.
6. Statistical Verification: For intermittent/flaky bugs, verify with 100 runs.
7. Terminate with an honest verdict: SUCCESS, PARTIAL, BLOCKED, or UNKNOWN.
"""


class AutonomousInvestigator:
    """Autonomous agent driving software forensic investigations in a closed reasoning loop."""

    def __init__(
        self,
        project_dir: Path,
        provider: Optional[BaseReasoningProvider] = None,
        use_sandbox: bool = True,
    ):
        self.project_dir = Path(project_dir).resolve()
        self.engine = InvestigationEngine(project_dir=self.project_dir, use_sandbox=use_sandbox)
        self.registry = ForensicToolRegistry(self.engine)
        self.provider = provider or HeuristicForensicDriver()

    def get_state_snapshot(self) -> Dict[str, Any]:
        """Compile complete current case state for the reasoning provider."""
        case = self.engine.state.case
        evidence = [e.to_ledger_dict() for e in self.engine.state.evidence_ledger.all()]
        hypotheses = [h.model_dump() for h in self.engine.state.hypothesis_manager.all()]

        experiments = []
        if self.engine.state.experiments_file.exists():
            with open(self.engine.state.experiments_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        experiments.append(json.loads(line.strip()))
                    except Exception:
                        pass

        return {
            "case": case.model_dump() if case else {},
            "stage": case.status.value if case else "intake",
            "evidence": evidence,
            "hypotheses": hypotheses,
            "experiments": experiments,
            "evidence_count": len(evidence),
            "hypothesis_count": len(hypotheses),
        }

    def investigate(
        self,
        problem_statement: str,
        title: Optional[str] = None,
        category: CaseCategory = CaseCategory.BUG,
        repro_command: Optional[str] = None,
        max_steps: int = 15,
        verbose: bool = True,
    ) -> str:
        """Run the autonomous investigation loop until conclusion or max_steps reached."""
        case_title = title or "Autonomous Investigation"
        case_id = f"CASE-{int(self.project_dir.stat().st_mtime)}"

        # Initial intake
        self.engine.intake(
            case_id=case_id,
            title=case_title,
            problem_statement=problem_statement,
            category=category,
        )
        if repro_command and self.engine.state.case:
            self.engine.state.case.reproduction_command = repro_command
            self.engine.state.save_case()

        if verbose:
            print_banner(case_id)
            console.print(f"[bold cyan]Initiating Autonomous Investigation Loop...[/bold cyan]")
            console.print(f"[bold]Problem:[/bold] {problem_statement}\n")

        tools = self.registry.get_tool_definitions()

        for step in range(1, max_steps + 1):
            state_snapshot = self.get_state_snapshot()

            # Check termination status
            term_status = TerminationManager.evaluate(self.engine.state)
            if term_status.can_terminate and self.engine.state.case.status == InvestigationStage.CLOSED:
                if verbose:
                    console.print(f"\n[bold green]✓ Termination condition satisfied: {term_status.reason}[/bold green]")
                break

            # Reason next step
            decision: ToolCall = self.provider.decide_next_step(
                case_state=state_snapshot,
                tools=tools,
                system_instruction=FORENSIC_AGENT_SYSTEM_PROMPT,
            )

            if verbose:
                thought_text = f"[italic cyan]Step {step}: {decision.thought}[/italic cyan]" if decision.thought else f"[cyan]Step {step}[/cyan]"
                console.print(f"\n{thought_text}")
                console.print(f"  [bold yellow]Action:[/bold yellow] [bold]{decision.name}[/bold]({json.dumps(decision.arguments, ensure_ascii=False)[:80]}...)")

            # Execute tool
            try:
                result = self.registry.execute_tool(decision.name, decision.arguments)
                if verbose:
                    console.print(f"  [bold green]Outcome:[/bold green] {json.dumps(result, ensure_ascii=False)[:100]}")
            except Exception as e:
                if verbose:
                    console.print(f"  [bold red]Action Error:[/bold red] {str(e)}")

            if decision.name == "conclude":
                break

        # Compile final report if not yet closed
        if self.engine.state.case and self.engine.state.case.status != InvestigationStage.CLOSED:
            report_md = self.engine.conclude(verdict=InvestigationVerdict.SUCCESS)
        else:
            report_path = self.engine.state.investigation_dir / "report.md"
            report_md = report_path.read_text(encoding="utf-8") if report_path.exists() else "# Report"

        if verbose:
            print_status_board(self.engine.state)

        return report_md
