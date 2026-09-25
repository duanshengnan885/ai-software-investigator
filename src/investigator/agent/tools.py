"""Forensic Tool Registry for Autonomous AI Investigator Agent.

Defines the forensic tool actions, argument schemas, and execution bindings.
"""

from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from investigator.engine.investigator import InvestigationEngine
from investigator.engine.protocol import CaseCategory, ExperimentOutcome, InvestigationVerdict


class ToolCall(BaseModel):
    """Represents a tool call decision made by the reasoning agent."""

    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    thought: str = Field(default="", description="The agent's forensic rationale for this action")


class ForensicToolRegistry:
    """Registry of actionable forensic tools callable by the AI Agent."""

    def __init__(self, engine: InvestigationEngine):
        self.engine = engine

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return JSON schemas of available forensic tools."""
        return [
            {
                "name": "intake",
                "description": "Initialize a new investigation case with problem statement and category.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "case_id": {"type": "string", "description": "Unique Case ID (e.g. CASE-2026-0001)"},
                        "title": {"type": "string", "description": "Concise case title"},
                        "problem_statement": {"type": "string", "description": "Original bug report or symptoms"},
                        "category": {"type": "string", "enum": ["bug", "performance", "reliability", "behavioral", "blackbox"]},
                    },
                    "required": ["title", "problem_statement"],
                },
            },
            {
                "name": "discover_environment",
                "description": "Probe and record host runtime environment, operating system, architecture, and python version.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "reproduce_problem",
                "description": "Execute a reproduction command to establish deterministic or statistical failure baseline.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repro_command": {"type": "string", "description": "Command to execute for reproduction"},
                        "runs": {"type": "integer", "description": "Number of trials (e.g. 1 for deterministic, 30 for flaky)"},
                        "expected_exit_code": {"type": "integer", "default": 0},
                    },
                    "required": ["repro_command"],
                },
            },
            {
                "name": "formulate_hypothesis",
                "description": "Register a new falsifiable hypothesis explaining the failure mechanism.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Concise hypothesis title"},
                        "description": {"type": "string", "description": "Detailed failure mechanism"},
                        "category": {"type": "string", "description": "Category (e.g. logic, concurrency, memory)"},
                        "hypothesis_id": {"type": "string", "description": "Optional explicit ID (e.g. H1)"},
                    },
                    "required": ["title", "description"],
                },
            },
            {
                "name": "execute_experiment",
                "description": "Execute an empirical experiment to support or refute a hypothesis.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Experiment title"},
                        "objective": {"type": "string", "description": "What question does this answer?"},
                        "expected_prediction": {"type": "string", "description": "Predicted observation if hypothesis is true"},
                        "command": {"type": "string", "description": "Command to run"},
                        "hypothesis_id": {"type": "string", "description": "Hypothesis tested by this experiment"},
                        "statistical_runs": {"type": "integer", "default": 1},
                        "expected_pass_code": {"type": "integer", "default": 0},
                        "expect_failure": {"type": "boolean", "default": False},
                    },
                    "required": ["title", "objective", "expected_prediction", "command"],
                },
            },
            {
                "name": "eliminate_hypothesis",
                "description": "Reject a hypothesis based on contradicting experiment evidence.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hypothesis_id": {"type": "string", "description": "ID of hypothesis to reject (e.g. H1)"},
                        "rationale": {"type": "string", "description": "Empirical rationale proving why it is falsified"},
                    },
                    "required": ["hypothesis_id", "rationale"],
                },
            },
            {
                "name": "identify_root_cause",
                "description": "Confirm a hypothesis as the verified Root Cause with causal proof.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hypothesis_id": {"type": "string", "description": "Hypothesis confirmed (e.g. H2)"},
                        "what": {"type": "string", "description": "What happened"},
                        "why": {"type": "string", "description": "Why it happened (mechanistic explanation)"},
                        "where": {"type": "string", "description": "Where it happened (file, line, function)"},
                        "how_confirmed": {"type": "string", "description": "Empirical proof / experiment backing"},
                    },
                    "required": ["hypothesis_id", "what", "why", "where", "how_confirmed"],
                },
            },
            {
                "name": "apply_minimal_fix",
                "description": "Apply a surgical code modification and compute diff blast radius.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_modifications": {
                            "type": "object",
                            "description": "Mapping from relative file path to new full content",
                        },
                        "rationales": {
                            "type": "object",
                            "description": "Mapping from file path to justification rationale",
                        },
                    },
                    "required": ["file_modifications", "rationales"],
                },
            },
            {
                "name": "verify_fix",
                "description": "Run post-fix reproduction trials (e.g. 100 runs) and regression tests to guarantee zero failures.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reproduction_command": {"type": "string", "description": "Reproduction command to verify"},
                        "verification_runs": {"type": "integer", "default": 10},
                        "regression_commands": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["reproduction_command"],
                },
            },
            {
                "name": "conclude",
                "description": "Terminate the investigation and compile the final forensic audit report.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "verdict": {"type": "string", "enum": ["SUCCESS", "PARTIAL", "BLOCKED", "UNKNOWN"]},
                        "remaining_uncertainties": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["verdict"],
                },
            },
        ]

    def execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch a tool call to the engine."""
        if name == "intake":
            case = self.engine.intake(
                case_id=args.get("case_id") or f"CASE-{int(self.engine.project_dir.stat().st_mtime)}",
                title=args["title"],
                problem_statement=args["problem_statement"],
                category=CaseCategory(args.get("category", "bug")),
            )
            return {"status": "ok", "case_id": case.case_id}

        elif name == "discover_environment":
            env = self.engine.discover_environment()
            return {"status": "ok", "environment": env}

        elif name == "reproduce_problem":
            res = self.engine.reproduce_problem(
                repro_command=args["repro_command"],
                runs=args.get("runs", 1),
                expected_exit_code=args.get("expected_exit_code", 0),
            )
            return {"status": "ok", "reproduction": res}

        elif name == "formulate_hypothesis":
            hypo = self.engine.formulate_hypothesis(
                title=args["title"],
                description=args["description"],
                category=args.get("category", "logic"),
                hypothesis_id=args.get("hypothesis_id"),
            )
            return {"status": "ok", "hypothesis_id": hypo.hypothesis_id, "status_value": hypo.status.value}

        elif name == "execute_experiment":
            exp = self.engine.execute_experiment(
                title=args["title"],
                objective=args["objective"],
                expected_prediction=args["expected_prediction"],
                command=args["command"],
                hypothesis_id=args.get("hypothesis_id"),
                statistical_runs=args.get("statistical_runs", 1),
                expected_pass_code=args.get("expected_pass_code", 0),
                expect_failure=args.get("expect_failure", False),
            )
            return {
                "status": "ok",
                "experiment_id": exp.experiment_id,
                "outcome": exp.outcome.value,
                "exit_code": exp.exit_code,
                "actual_result": exp.actual_result,
            }

        elif name == "eliminate_hypothesis":
            hypo = self.engine.reject_hypothesis(
                hypothesis_id=args["hypothesis_id"],
                rationale=args["rationale"],
            )
            return {"status": "ok", "hypothesis_id": hypo.hypothesis_id, "status_value": hypo.status.value}

        elif name == "identify_root_cause":
            hypo = self.engine.identify_root_cause(
                hypothesis_id=args["hypothesis_id"],
                what=args["what"],
                why=args["why"],
                where=args["where"],
                how_confirmed=args["how_confirmed"],
            )
            return {"status": "ok", "confirmed_hypothesis": hypo.hypothesis_id}

        elif name == "apply_minimal_fix":
            diff = self.engine.apply_minimal_fix(
                file_modifications=args["file_modifications"],
                rationales=args["rationales"],
            )
            return {
                "status": "ok",
                "files_changed": len(diff.files),
                "lines_added": diff.total_added,
                "lines_removed": diff.total_removed,
                "blast_radius": diff.blast_radius,
                "is_minimal": diff.is_minimal_fix,
            }

        elif name == "verify_fix":
            res = self.engine.verify_fix(
                reproduction_command=args["reproduction_command"],
                verification_runs=args.get("verification_runs", 10),
                regression_commands=args.get("regression_commands"),
            )
            return {"status": "ok", "verification": res}

        elif name == "conclude":
            report_md = self.engine.conclude(
                verdict=InvestigationVerdict(args["verdict"]),
                remaining_uncertainties=args.get("remaining_uncertainties"),
            )
            return {"status": "ok", "report_length": len(report_md)}

        else:
            raise ValueError(f"Unknown forensic tool: {name}")
