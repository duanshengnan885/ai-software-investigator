"""Rich Terminal User Interface for AI Software Investigator.

Renders live status boards, hypothesis matrices, experiment cards,
and confidence gauges.
"""

from typing import Any, Dict, List, Optional
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from investigator.engine.protocol import ConfidenceLevel, HypothesisStatus
from investigator.engine.state import InvestigationState

# Ensure safe encoding for Windows command line
try:
    if sys.platform == "win32" and sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

console = Console(force_terminal=True, soft_wrap=True)


def print_banner(case_id: Optional[str] = None) -> None:
    """Render the forensic investigator banner."""
    header = (
        "[bold cyan]╔════════════════════════════════════════════════════════════════╗[/bold cyan]\n"
        "[bold cyan]║[/bold cyan]             [bold white]AI SOFTWARE INVESTIGATOR (ASI)[/bold white]                     [bold cyan]║[/bold cyan]\n"
        "[bold cyan]║[/bold cyan]    [italic dim]Autonomous Forensic Investigation Engine for Software Behavior[/italic dim]   [bold cyan]║[/bold cyan]\n"
        "[bold cyan]╚════════════════════════════════════════════════════════════════╝[/bold cyan]"
    )
    console.print(header)
    if case_id:
        console.print(f"[bold yellow]CASE ID:[/bold yellow] [bold white]{case_id}[/bold white]\n")


def print_stage_checklist(current_stage_name: str) -> None:
    """Render the forensic investigation stage checklist."""
    stages = [
        ("intake", "Project Intake"),
        ("environment_discovery", "Environment Discovery"),
        ("reproduction", "Problem Reproduction"),
        ("hypothesis_generation", "Hypothesis Generation"),
        ("experiment_execution", "Empirical Experiments"),
        ("hypothesis_elimination", "Hypothesis Elimination"),
        ("root_cause_identification", "Root Cause Identification"),
        ("minimal_fix", "Minimal Fix & Diff Reasoning"),
        ("independent_verification", "Independent Verification"),
        ("report_generation", "Forensic Report"),
    ]

    table = Table(title="Investigation Lifecycle", show_header=False, box=None)
    table.add_column("Index", style="cyan", width=4)
    table.add_column("Stage", style="white", width=30)
    table.add_column("Status", width=15)

    found_current = False
    for idx, (stage_key, label) in enumerate(stages, 1):
        if stage_key == current_stage_name:
            found_current = True
            status_text = Text("RUNNING ⏳", style="bold yellow")
        elif not found_current:
            status_text = Text("DONE ✓", style="bold green")
        else:
            status_text = Text("PENDING", style="dim")

        table.add_row(f"[{idx}]", label, status_text)

    console.print(Panel(table, title="[bold]Investigation Stages[/bold]", border_style="cyan"))


def print_hypotheses_table(state: InvestigationState) -> None:
    """Render hypotheses table with colored status badges."""
    hypotheses = state.hypothesis_manager.all()
    table = Table(title="Hypothesis Ledger", border_style="blue")
    table.add_column("ID", style="bold cyan", width=6)
    table.add_column("Hypothesis Title", style="white", min_width=25)
    table.add_column("Status", justify="center", width=15)
    table.add_column("Confidence", justify="right", width=12)
    table.add_column("Supporting", justify="center", width=12)
    table.add_column("Contradicting", justify="center", width=14)

    status_styles = {
        HypothesisStatus.UNTESTED: "dim white",
        HypothesisStatus.PLAUSIBLE: "yellow",
        HypothesisStatus.SUPPORTED: "green",
        HypothesisStatus.WEAKENED: "magenta",
        HypothesisStatus.REJECTED: "bold red",
        HypothesisStatus.CONFIRMED: "bold green on black",
    }

    for h in hypotheses:
        style = status_styles.get(h.status, "white")
        badge = f"[{style}][{h.status.value}][/{style}]"
        supp = str(len(h.supporting_evidence))
        contra = str(len(h.contradicting_evidence))
        conf_str = f"{h.confidence*100:.0f}%"

        table.add_row(h.hypothesis_id, h.title, badge, conf_str, supp, contra)

    console.print(table)


def print_evidence_table(state: InvestigationState, limit: int = 8) -> None:
    """Render recent entries from the evidence ledger."""
    evidence_items = state.evidence_ledger.all()[-limit:]
    table = Table(title=f"Forensic Evidence Ledger (Recent {len(evidence_items)})", border_style="green")
    table.add_column("ID", style="bold cyan", width=7)
    table.add_column("Status", style="yellow", width=12)
    table.add_column("Source", style="dim", width=20)
    table.add_column("Description", style="white")

    for e in evidence_items:
        table.add_row(e.evidence_id, e.claim_status.value, e.source, e.description)

    console.print(table)


def print_confidence_card(score: float, level: ConfidenceLevel, basis: List[str]) -> None:
    """Render the empirical confidence gauge and itemized justification."""
    pct = score * 100
    color = "green" if level == ConfidenceLevel.HIGH else ("yellow" if level == ConfidenceLevel.MEDIUM else "red")

    # Render a text-based progress bar
    filled = int(score * 20)
    bar = "█" * filled + "░" * (20 - filled)

    content = Text()
    content.append(f"Confidence Level: ", style="bold")
    content.append(f"{level.value} ({pct:.1f}%)\n", style=f"bold {color}")
    content.append(f"Score Gauge: [{bar}]\n\n", style=color)
    content.append("Empirical Basis:\n", style="bold underline")
    for b in basis:
        content.append(f"  - {b}\n", style="white")

    console.print(Panel(content, title="[bold]Empirical Confidence Assessment[/bold]", border_style=color))


def print_status_board(state: InvestigationState) -> None:
    """Print complete consolidated status board."""
    case = state.case
    if not case:
        console.print("[yellow]No active case found in state.[/yellow]")
        return

    print_banner(case.case_id)
    console.print(f"[bold]Title:[/bold] {case.title}")
    console.print(f"[bold]Category:[/bold] {case.category.value} | [bold]Status:[/bold] {case.status.value}\n")

    print_stage_checklist(case.status.value)
    console.print("")
    print_hypotheses_table(state)
    console.print("")
    print_evidence_table(state)
    console.print("")

    if case.confidence_score > 0:
        print_confidence_card(case.confidence_score, case.confidence_level, case.confidence_basis)
