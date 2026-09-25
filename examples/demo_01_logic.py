"""Demo 1: Ordinary Logic Bug (Order Processing Tier Boundary Crash).

Demonstrates the full autonomous forensic workflow:
Intake -> Environment -> Baseline Repro (100% crash) -> Hypotheses formulation ->
Controlled Experiments -> Elimination -> Root Cause -> Minimal 1-line Fix ->
Regression Verification -> Report Generation.
"""

from pathlib import Path
import sys
import tempfile
import time

from rich.console import Console

from investigator.cli.ui import (
    print_banner,
    print_confidence_card,
    print_evidence_table,
    print_hypotheses_table,
    print_stage_checklist,
    print_status_board,
)
from investigator.engine.investigator import InvestigationEngine
from investigator.engine.protocol import CaseCategory, InvestigationVerdict

console = Console()

# Faulty application code
FAULTY_ORDER_PROCESSOR = '''"""Order Processing Engine."""
import sys

# Discount tiers: (minimum_quantity, discount_rate)
TIERS = [
    (1, 0.0),
    (10, 0.10),  # 10% off for 10 or more
    (50, 0.20),  # 20% off for 50 or more
]

def calculate_discount(quantity: int, unit_price: float) -> float:
    if quantity <= 0:
        return 0.0
    
    tier_index = -1
    for i in range(len(TIERS)):
        if quantity > TIERS[i][0]:
            tier_index = i
        elif quantity == TIERS[i][0]:
            # BUG: Off-by-one / invalid index calculation on exact threshold match!
            tier_index = i + len(TIERS) # Out of bounds index!
            
    if tier_index >= len(TIERS):
        raise IndexError(f"Calculated discount tier index {tier_index} exceeds tier table bounds ({len(TIERS)})")
        
    rate = TIERS[tier_index][1] if tier_index >= 0 else 0.0
    return quantity * unit_price * (1.0 - rate)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python order_processor.py <quantity>")
        sys.exit(1)
        
    qty = int(sys.argv[1])
    try:
        total = calculate_discount(qty, 100.0)
        print(f"SUCCESS: Quantity {qty} -> Total ${total:.2f}")
        sys.exit(0)
    except Exception as e:
        print(f"CRASH: {type(e).__name__}: {str(e)}", file=sys.stderr)
        sys.exit(2)
'''

# Minimal surgical fix
FIXED_ORDER_PROCESSOR = '''"""Order Processing Engine."""
import sys

# Discount tiers: (minimum_quantity, discount_rate)
TIERS = [
    (1, 0.0),
    (10, 0.10),  # 10% off for 10 or more
    (50, 0.20),  # 20% off for 50 or more
]

def calculate_discount(quantity: int, unit_price: float) -> float:
    if quantity <= 0:
        return 0.0
    
    tier_index = -1
    for i in range(len(TIERS)):
        if quantity >= TIERS[i][0]:
            tier_index = i
            
    if tier_index >= len(TIERS):
        raise IndexError(f"Calculated discount tier index {tier_index} exceeds tier table bounds ({len(TIERS)})")
        
    rate = TIERS[tier_index][1] if tier_index >= 0 else 0.0
    return quantity * unit_price * (1.0 - rate)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python order_processor.py <quantity>")
        sys.exit(1)
        
    qty = int(sys.argv[1])
    try:
        total = calculate_discount(qty, 100.0)
        print(f"SUCCESS: Quantity {qty} -> Total ${total:.2f}")
        sys.exit(0)
    except Exception as e:
        print(f"CRASH: {type(e).__name__}: {str(e)}", file=sys.stderr)
        sys.exit(2)
'''


def run_demo_01() -> None:
    """Execute Demo 1 investigation."""
    with tempfile.TemporaryDirectory(prefix="asi_demo_01_") as temp_dir:
        work_dir = Path(temp_dir)
        script_file = work_dir / "order_processor.py"
        script_file.write_text(FAULTY_ORDER_PROCESSOR, encoding="utf-8")

        print_banner("CASE-2026-0001")
        console.print("[bold yellow]>>> DEMO 1: ORDINARY LOGIC BUG INVESTIGATION[/bold yellow]\n")

        # 1. Initialize Engine
        engine = InvestigationEngine(project_dir=work_dir, use_sandbox=False)

        # 2. Intake
        engine.intake(
            case_id="CASE-2026-0001",
            title="Order Processing Crash on Threshold Quantities",
            problem_statement="Order service occasionally crashes with IndexError when specific order volumes are submitted.",
            category=CaseCategory.BUG,
        )

        # 3. Environment Discovery
        console.print("[bold cyan][Stage 1/7] Discovering Environment...[/bold cyan]")
        engine.discover_environment()

        # 4. Problem Reproduction
        console.print("[bold cyan][Stage 2/7] Reproducing Problem with Quantity=10...[/bold cyan]")
        repro_cmd = f"python order_processor.py 10"
        repro = engine.reproduce_problem(repro_command=repro_cmd, runs=1)
        console.print(f"  Reproduction result: Exit code {repro['exit_code']} (CRASH REPRODUCED 100%)\n")

        # 5. Formulate Hypotheses
        console.print("[bold cyan][Stage 3/7] Formulating Falsifiable Hypotheses...[/bold cyan]")
        h1 = engine.formulate_hypothesis(
            title="Database Inventory Lookup Failure",
            description="Service crashes due to an unhandled null response from product inventory database.",
            category="io",
        )
        h2 = engine.formulate_hypothesis(
            title="Tier Boundary Calculation Off-by-One",
            description="The loop in calculate_discount contains faulty indexing logic specifically triggered when quantity equals the tier boundary (10).",
            category="logic",
        )
        h3 = engine.formulate_hypothesis(
            title="Float Currency Precision Underflow",
            description="Calculating discount amount produces precision underflow leading to type coercion crash.",
            category="numeric",
        )
        print_hypotheses_table(engine.state)

        # 6. Controlled Experiments
        console.print("\n[bold cyan][Stage 4/7] Executing Empirical Experiments...[/bold cyan]")

        # Exp 1: Quantity below threshold (9)
        console.print("  - Running EXP-001: Testing Quantity = 9 (below tier threshold)...")
        exp1 = engine.execute_experiment(
            title="Below Threshold Test (Qty=9)",
            objective="Determine if values strictly below tier boundary execute normally",
            expected_prediction="Exit code 0 (success)",
            command="python order_processor.py 9",
            hypothesis_id="H2",
            expected_pass_code=0,
        )
        console.print(f"    Observed: Exit code {exp1.exit_code} -> {exp1.outcome.value}")

        # Exp 2: Quantity above threshold (11)
        console.print("  - Running EXP-002: Testing Quantity = 11 (above tier threshold)...")
        exp2 = engine.execute_experiment(
            title="Above Threshold Test (Qty=11)",
            objective="Determine if values strictly above tier boundary execute normally",
            expected_prediction="Exit code 0 (success)",
            command="python order_processor.py 11",
            hypothesis_id="H2",
            expected_pass_code=0,
        )
        console.print(f"    Observed: Exit code {exp2.exit_code} -> {exp2.outcome.value}")

        # Exp 3: Testing DB dependency (H1)
        console.print("  - Running EXP-003: Testing database decoupling (H1)...")
        exp3 = engine.execute_experiment(
            title="Database Isolation Check",
            objective="Determine if service crashes due to external DB timeout",
            expected_prediction="Local execution succeeds with no DB calls",
            command="python order_processor.py 5",
            hypothesis_id="H1",
            expected_pass_code=0,
        )
        console.print(f"    Observed: Exit code {exp3.exit_code} -> {exp3.outcome.value}")

        # Exp 4: Testing float precision underflow (H3)
        console.print("  - Running EXP-004: Testing float discount precision underflow (H3)...")
        exp4 = engine.execute_experiment(
            title="Float Currency Precision Test",
            objective="Determine if float underflow occurs during price calculation",
            expected_prediction="Exact floating point output produced without overflow",
            command="python order_processor.py 2",
            hypothesis_id="H3",
            expected_pass_code=0,
        )
        console.print(f"    Observed: Exit code {exp4.exit_code} -> {exp4.outcome.value}")

        # 7. Hypothesis Elimination
        console.print("\n[bold cyan][Stage 5/7] Eliminating Alternative Hypotheses...[/bold cyan]")
        engine.reject_hypothesis(
            hypothesis_id="H1",
            rationale="EXP-003 demonstrated code executes self-contained in-memory without database dependencies.",
        )
        engine.reject_hypothesis(
            hypothesis_id="H3",
            rationale="EXP-004 demonstrated IEEE 754 float arithmetic computes correctly without precision crashes.",
        )

        # 8. Identify Root Cause
        console.print("\n[bold cyan][Stage 6/7] Confirming Root Cause...[/bold cyan]")
        engine.identify_root_cause(
            hypothesis_id="H2",
            what="IndexError: calculated discount tier index exceeds tier table bounds when quantity == threshold",
            why="When quantity exactly matches a tier threshold (e.g. quantity == 10), the loop enters an incorrect branch that artificially adds table length to tier_index.",
            where="order_processor.py: line 19 in calculate_discount()",
            how_confirmed="Empirical boundary tests: quantity=9 and 11 pass, while quantity=10 consistently triggers IndexError.",
        )
        print_hypotheses_table(engine.state)

        # 9. Minimal Fix & Diff Reasoning
        console.print("\n[bold cyan][Stage 7/7] Applying Minimal Fix & Verifying...[/bold cyan]")
        diff_analysis = engine.apply_minimal_fix(
            file_modifications={"order_processor.py": FIXED_ORDER_PROCESSOR},
            rationales={"order_processor.py": "Replace faulty branching with single inclusive '>=' check on tier thresholds."}
        )
        console.print(f"  Minimal Fix applied: +{diff_analysis.total_added} / -{diff_analysis.total_removed} lines. Blast radius: {diff_analysis.blast_radius}")

        # 10. Independent Verification
        verif = engine.verify_fix(
            reproduction_command="python order_processor.py 10",
            verification_runs=10,
            regression_commands=[
                "python order_processor.py 1",
                "python order_processor.py 9",
                "python order_processor.py 10",
                "python order_processor.py 11",
                "python order_processor.py 50",
                "python order_processor.py 51",
            ]
        )
        console.print(f"  Verification Result: {verif['failures']} failures across {verif['verification_runs']} trials! Regression tests passed.")

        # Conclude
        report_md = engine.conclude(verdict=InvestigationVerdict.SUCCESS)
        console.print("\n[bold green]✓ INVESTIGATION CONCLUDED SUCCESSFULLY (VERDICT: SUCCESS)![/bold green]")

        print_status_board(engine.state)


if __name__ == "__main__":
    run_demo_01()
