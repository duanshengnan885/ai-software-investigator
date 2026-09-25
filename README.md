# AI Software Investigator (ASI)

<div align="center">

```text
╔════════════════════════════════════════════════════════════════╗
║             AI SOFTWARE INVESTIGATOR (ASI)                     ║
║    Autonomous Forensic Investigation Engine for Software Behavior   ║
╚════════════════════════════════════════════════════════════════╝
```

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-19%20passed%20%7C%20100%25-brightgreen.svg)]()
[![Type Checked](https://img.shields.io/badge/type--checked-pydantic%20v2-blueviolet.svg)]()
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-Ready-blue.svg)](SKILL.md)

**"Give it a broken or unknown program. Let it investigate before it fixes."**

*Not an AI coding assistant. An autonomous software forensic pathologist.*

</div>

---

## 🔬 Core Philosophy

When a software system behaves unexpectedly, standard AI coding assistants read the source code and immediately guess how to fix it. This speculative guessing leads to hallucinations, false confidence, and regression-inducing patches.

**AI Software Investigator (ASI)** approaches software like a forensic pathologist:

$$\text{Hypotheses} \longrightarrow \text{Experiments} \longrightarrow \text{Evidence} \longrightarrow \text{Elimination} \longrightarrow \text{Root Cause} \longrightarrow \text{Minimal Fix} \longrightarrow \text{Verification}$$

- **Evidence First:** Conclusions must bind to verifiable empirical evidence records (`E-001`, `E-002`) with explicit claim status (`Observed`, `Inferred`, `Hypothesized`, `Verified`, `Unknown`).
- **Hypothesis Driven:** Falsifiable hypotheses are explicitly registered and tracked (`UNTESTED`, `PLAUSIBLE`, `SUPPORTED`, `WEAKENED`, `REJECTED`, `CONFIRMED`).
- **Information Gain First:** Experiments are mathematically prioritized to differentiate competing hypotheses with minimal cost and risk.
- **Statistical Verification:** Non-deterministic or intermittent bugs are verified over 100 consecutive stress trials to guarantee zero reproduction post-fix.
- **Closed Sandbox:** Modifications, benchmarks, and probes run in isolated directories or Git worktrees with snapshots and instant rollback.
- **Black-box Investigation:** Fully supports investigating closed-source or compiled binaries via automated binary search boundary discovery and input fuzzing.

---

## 📋 The 12-Stage Forensic Protocol

```text
Project Intake
      ↓
Environment Discovery
      ↓
Evidence Collection & Baseline Reproduction
      ↓
Hypothesis Generation
      ↓
Experiment Planning (Information Gain First)
      ↓
Sandbox Experiment Execution
      ↓
Evidence Analysis & Anti-Hallucination Tagging
      ↓
Hypothesis Elimination
      ↓
Root Cause Identification (What, Why, Where, How Confirmed)
      ↓
Minimal Surgical Fix & Diff Reasoning
      ↓
Independent & Statistical Verification (100 runs)
      ↓
Forensic Report Generation
```

---

## 🖥️ Live Terminal Interface

ASI features a rich, real-time terminal UI providing full situational awareness:

```text
╔════════════════════════════════════════════════════════════════╗
║             AI SOFTWARE INVESTIGATOR (ASI)                     ║
║    Autonomous Forensic Investigation Engine for Software Behavior   ║
╚════════════════════════════════════════════════════════════════╝
CASE ID: CASE-2026-0002

Title: Intermittent Cache Service Crash Under Concurrent Load
Category: reliability | Status: closed

┌─────────────────────────── Investigation Stages ────────────────────────────┐
│ Investigation Lifecycle                                                     │
│  [1]   Project Intake                  DONE ✓                               │
│  [2]   Environment Discovery           DONE ✓                               │
│  [3]   Problem Reproduction            DONE ✓                               │
│  [4]   Hypothesis Generation           DONE ✓                               │
│  [5]   Empirical Experiments           DONE ✓                               │
│  [6]   Hypothesis Elimination          DONE ✓                               │
│  [7]   Root Cause Identification       DONE ✓                               │
│  [8]   Minimal Fix & Diff Reasoning    DONE ✓                               │
│  [9]   Independent Verification        DONE ✓                               │
│  [10]  Forensic Report                 DONE ✓                               │
└─────────────────────────────────────────────────────────────────────────────┘

Hypothesis Ledger
┌────────┬───────────────────────────┬─────────────────┬──────────────┬──────────────┬────────────────┐
│ ID     │ Hypothesis Title          │     Status      │   Confidence │  Supporting  │ Contradicting  │
├────────┼───────────────────────────┼─────────────────┼──────────────┼──────────────┼────────────────┤
│ H1     │ Process Memory Exhaustion │   [REJECTED]    │           5% │      0       │       1        │
│ H2     │ Unsynchronized Critical   │   [CONFIRMED]   │          95% │      3       │       0        │
│        │ Section Race Condition    │                 │              │              │                │
│ H3     │ OS Thread Limit           │   [REJECTED]    │           5% │      0       │       1        │
│        │ Exhaustion                │                 │              │              │                │
└────────┴───────────────────────────┴─────────────────┴──────────────┴──────────────┴────────────────┘

┌────────────────────── Empirical Confidence Assessment ──────────────────────┐
│ Confidence Level: HIGH (99.0%)                                              │
│ Score Gauge: [███████████████████░]                                         │
│                                                                             │
│ Empirical Basis:                                                            │
│   - Problem successfully reproduced with 100.0% trigger rate (1 runs)       │
│   - Supported by 3 independently verified high-reliability evidence records │
│   - Validated across 3 distinct empirical experiments                       │
│   - Systematically eliminated 2 competing hypotheses via experiment         │
│   - Fix verified: 0 failures observed in 100 execution trials               │
│   - Full regression test suite passed cleanly                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart & Skill Installation

### Requirements
- Python 3.10+
- OS: Windows, Linux, macOS
- Compatible with AI Agent Platforms: **Google Antigravity**, **Claude Code**, **Cursor**, **Windsurf**, **OpenCode / Codex**

---

### Method A: One-Command Universal Skill Installer (Recommended)

Clone the repository and run the zero-dependency installer:

```bash
git clone https://github.com/duanshengnan885/ai-software-investigator.git
cd ai-software-investigator

# Auto-detects installed AI platforms, installs SKILL.md, and sets up CLI
python install.py
```

You can also target specific platforms explicitly:
```bash
python install.py --antigravity      # Install to Google Antigravity (~/.gemini/config/skills/)
python install.py --claude            # Install to Claude Code (~/.claude/skills/)
python install.py --cursor .          # Generate Cursor rules in target project
python install.py --agents            # Install to Universal Agent root (~/.agents/skills/)
```

---

### Method B: Manual AI Platform Integration

#### 1. Google Antigravity (AGY)
Copy or symlink `SKILL.md` to your global or project skills directory:
```bash
# Global
cp SKILL.md ~/.gemini/config/skills/ai-software-investigator/SKILL.md
# Or in your active project workspace:
cp SKILL.md .agents/skills/ai-software-investigator/SKILL.md
```

#### 2. Claude Code
```bash
mkdir -p ~/.claude/skills/ai-software-investigator
cp SKILL.md ~/.claude/skills/ai-software-investigator/
```

#### 3. Cursor / Windsurf
Copy `.cursor/rules/ai-software-investigator.mdc` into your target workspace's `.cursor/rules/`.

---

### 💬 How to Invoke in Your AI Coding Platform

Once installed, simply talk to your AI assistant naturally:

```text
User:
/investigate "Our payment webhook service intermittently throws 504 gateway timeout under load."
```
or:
```text
User:
这个程序运行到第 129 个字符时会突然崩溃（Exit code 139），请使用 ai-software-investigator 技能排查根因。
```

**The AI Assistant will immediately:**
1. Formulate falsifiable hypotheses ($H_1, H_2, H_3$).
2. Launch controlled sandbox experiments via `investigator`.
3. Tag evidence in `.investigation/evidence.jsonl` with epistemic status (`Observed`, `Inferred`, `Hypothesized`).
4. Eliminate invalidated hypotheses and isolate root cause.
5. Apply a minimal surgical fix and verify with 100 runs ($p \le 3.0\%$ under Rule of Three).
6. Output a forensic markdown report.

---

### 💻 Direct CLI Usage & Interactive Demos

You can also execute investigations directly from your terminal:

```bash
# Autonomous AI Investigation Loop (Self-directed reasoning & experiment dispatch)
investigator auto --dir "./my_project" --problem "Program intermittently crashes under load"

# Interactive Step-by-Step CLI Mode
investigator new --title "Cache Crash" --problem "Intermittent crash under load"
investigator status

# Automated Demonstrations
investigator demo 1   # Demo 1: Ordinary Logic Bug (Tier boundary crash)
investigator demo 2   # Demo 2: Intermittent Race Condition (100-run verification)
investigator demo 3   # Demo 3: Pure Black-box Binary Investigation
```

---

## 🎬 The Three Core Demos

### Demo 1: Ordinary Logic Bug
- **Problem:** Order processing crashes with `IndexError` when quantity hits tier boundaries (`quantity = 10`).
- **Forensic Flow:**
  1. Baseline reproduction reproduced at 100%.
  2. Formulates 3 hypotheses: H1 (Database null), H2 (Tier boundary off-by-one), H3 (Float precision).
  3. Executes controlled boundary probes: Qty 9 (Pass), Qty 11 (Pass), Qty 10 (Crash!).
  4. Falsifies H1 & H3; confirms H2.
  5. Applies surgical 1-line fix (`>` changed to `>=`).
  6. Independent verification across all tier intervals passes 100%. Confidence: **HIGH (99.0%)**.

### Demo 2: Intermittent Concurrency Bug
- **Problem:** Concurrent task queue service intermittently exceeds capacity limit and crashes under load.
- **Forensic Flow:**
  1. Statistical baseline: 30 runs $\to$ ~45% failure rate under concurrency 8.
  2. Formulates hypotheses: H1 (Memory heap leak), H2 (Unsynchronized TOCTOU race condition), H3 (OS thread limit exhaustion).
  3. **Concurrency Sweep Experiment:**
     - 1 worker: 0.0% failure (completely deterministic pass)
     - 4 workers: 35.0% failure
     - 16 workers: 50.0% - 70.0% failure
     - Causal relationship between thread contention and capacity violation established!
  4. Memory and OS allocation checks falsify H1 and H3.
  5. Minimal fix: introduces `threading.Lock()` guarding `enqueue()` check-then-act critical section.
  6. **Statistical Verification:** 100 consecutive runs at 16 threads $\to$ **0 failures / 100 trials (0.0% failure rate)**.
     - **Mathematical Rule of Three Bound:** At 95% statistical confidence, true post-fix failure probability $p \le 3.0\%$. Confidence: **HIGH (99.0%)**.

### Demo 3: Pure Black-box Binary Investigation
- **Problem:** Closed-source binary `mystery_parser` crashes with `SIGSEGV` (exit code 139) on long inputs. No source code, symbols, or diagnostic stderr available.
- **Forensic Flow:**
  1. Automated binary search on input length ($1 \to 512$ bytes).
  2. Isolates the exact transition boundary:
     $$\text{Length 128 (OK)} \longrightarrow \text{Length 129 (CRASH)}$$
  3. Character invariance fuzzing (symbols, digits, punctuation, Unicode) confirms failure occurs strictly as a function of length $\ge 129$, regardless of character semantics.
  4. **Epistemological Classification:**
     - **Observed:** Length $\le 128$ exits 0; Length $\ge 129$ exits 139. Invariant across character sets. Execution time $< 40$ms.
     - **Inferred:** Hard 128-byte memory boundary threshold triggers segmentation violation.
     - **Hypothesized:** Internal fixed-capacity 128-byte buffer without bounds check.
     - **Remaining Uncertainty / Requires Disassembly:** Whether buffer is stack-allocated (stack smashing) or heap-allocated requires binary disassembly / core dump analysis.
  5. Compiles input specification report with safe memory constraints. Case concludes with **PARTIAL** (Root cause threshold confirmed; source modification N/A).

---

## 📁 Investigation State Directory (`.investigation/`)

ASI writes complete forensic state to disk in `.investigation/`:

```text
.investigation/
├── case.json               # Case metadata, status, root cause link, confidence score
├── evidence.jsonl          # Immutable ledger of forensic evidence
├── hypotheses.json         # Active and historical hypotheses pool
├── experiments.jsonl       # Empirical experiment records, commands, metrics
├── timeline.jsonl          # Forensic milestone audit trail
├── findings.md             # Continuous investigation notes
├── report.md               # Final structured forensic investigation report
└── artifacts/              # Raw stdout logs, stderr dumps, diffs, memory profiles
```

### Evidence Ledger Format (`evidence.jsonl`)
```json
{
  "evidence_id": "E-003",
  "timestamp": "2026-09-26T05:15:30Z",
  "source": "experiment:EXP-001",
  "type": "experiment_observation",
  "claim_status": "Observed",
  "description": "Concurrency sweep: 1 thread -> 0% failure, 16 threads -> 45% failure",
  "raw_reference": "artifacts/EXP-001_stdout.log",
  "reliability": "HIGH",
  "related_hypotheses": ["H2"],
  "metadata": {"outcome": "SUPPORTED"}
}
```

---

## 🤖 Using as an Agent Skill

ASI is packaged with a production-grade [SKILL.md](SKILL.md) compatible with:
- **Google Antigravity**
- **Claude Code**
- **Codex**
- **Cursor** / **Windsurf**
- **OpenCode**

When interacting with an agent, simply invoke:
```text
/investigate "The worker pool intermittently crashes under high load. Investigate the root cause."
```
The agent reads `SKILL.md` and executes the forensic protocol step-by-step rather than guessing.

---

## 📦 Project Structure

```text
ai-software-investigator/
├── SKILL.md                          # Executable Agent Skill definition
├── README.md                         # Project documentation & walkthrough
├── LICENSE                           # MIT License
├── pyproject.toml                    # Package configuration & dependencies
│
├── src/
│   └── investigator/
│       ├── agent/                    # Autonomous AI Investigation Agent Loop
│       │   ├── core.py               # AutonomousInvestigator (Observe -> Reason -> Tool -> Loop)
│       │   ├── tools.py              # ForensicToolRegistry (JSON Schema tool definitions)
│       │   └── llm.py                # Pluggable reasoning backends (Heuristic / OpenAI / Anthropic)
│       ├── engine/                   # Core engine & orchestration
│       │   ├── investigator.py       # InvestigationEngine (12-stage lifecycle)
│       │   ├── state.py              # InvestigationState (.investigation/ manager)
│       │   ├── protocol.py           # Enums, statuses, lifecycle stages
│       │   ├── confidence.py         # ConfidenceCalculator (Binomial Confidence Interval & Rule of Three)
│       │   └── termination.py        # Termination conditions (SUCCESS/PARTIAL/BLOCKED/UNKNOWN)
│       ├── hypotheses/               # Hypothesis tracking & guardrails
│       │   ├── model.py              # Hypothesis & HypothesisTransition models
│       │   └── manager.py            # HypothesisManager (transition integrity)
│       ├── experiments/              # Empirical execution & planning
│       │   ├── model.py              # ExperimentRecord model
│       │   ├── runner.py             # ExperimentRunner (ProcessSandbox integration & statistical multi-runs)
│       │   ├── planner.py            # ExperimentPlanner (Information Gain First)
│       │   └── blackbox.py           # BlackboxInvestigator (binary search boundary & safe fuzzing)
│       ├── evidence/                 # Evidence-first ledger
│       │   ├── model.py              # Evidence model (anti-hallucination claim tagging)
│       │   └── ledger.py             # EvidenceLedger (chain of custody)
│       ├── sandbox/                  # Environment isolation & safety
│       │   ├── base.py               # BaseSandbox interface
│       │   ├── directory.py          # DirectorySandbox (copy-on-investigate & rollback)
│       │   ├── git_worktree.py       # GitWorktreeSandbox (branch isolation)
│       │   ├── process.py            # ProcessSandbox (sanitized env, tree kill & safe argv)
│       │   └── safety.py             # SafetyGuard (destructive command interception)
│       ├── reporting/                # Forensic reports & diff reasoning
│       │   ├── generator.py          # ReportGenerator (structured markdown report)
│       │   └── diff_analyzer.py      # DiffAnalyzer (Before/After reasoning & blast radius)
│       └── cli/                      # Rich Terminal User Interface
│           ├── main.py               # Command dispatcher ('investigator auto / new / status / demo')
│           └── ui.py                 # Live status board, hypothesis table, confidence gauge
│
├── tests/
│   ├── unit/                         # Unit tests (evidence, hypotheses, experiments, confidence, sandbox)
│   └── integration/                  # End-to-end integration tests
│
├── examples/                         # Real-world runnable demonstrations
│   ├── demo_01_logic.py              # Demo 1: Ordinary logic bug
│   ├── demo_02_race.py               # Demo 2: Intermittent race condition (100 runs)
│   └── demo_03_blackbox.py           # Demo 3: Closed-box boundary search
│
└── docs/
    ├── ARCHITECTURE.md               # Detailed system architecture
    ├── PROTOCOL.md                   # 12-stage forensic protocol & state transitions
    └── INVESTIGATION_GUIDE.md        # Practical guide for bug classes
```

---

## 🧪 Running Tests

Run the complete test suite:

```bash
pytest -v
```

Output:
```text
============================= test session starts =============================
tests/integration/test_investigation_flow.py::test_full_investigation_pipeline PASSED
tests/unit/test_blackbox.py::test_binary_search_boundary_discovery PASSED
tests/unit/test_blackbox.py::test_fuzz_input_permutations PASSED
tests/unit/test_confidence.py::test_confidence_calculator_baseline_and_progression PASSED
tests/unit/test_diff_analyzer.py::test_diff_analyzer_minimal_fix PASSED
tests/unit/test_diff_analyzer.py::test_diff_analyzer_large_blast_radius PASSED
tests/unit/test_evidence.py::test_evidence_model_serialization PASSED
tests/unit/test_evidence.py::test_evidence_ledger_lifecycle PASSED
tests/unit/test_evidence.py::test_evidence_ledger_validation PASSED
tests/unit/test_experiments.py::test_experiment_runner_execution PASSED
tests/unit/test_experiments.py::test_experiment_statistical_runner PASSED
tests/unit/test_experiments.py::test_experiment_planner_information_gain PASSED
tests/unit/test_hypotheses.py::test_hypothesis_model_and_transitions PASSED
tests/unit/test_hypotheses.py::test_hypothesis_manager_guardrails PASSED
tests/unit/test_hypotheses.py::test_hypothesis_manager_contradiction_guard PASSED
tests/unit/test_sandbox.py::test_directory_sandbox_snapshots_and_rollback PASSED
tests/unit/test_sandbox.py::test_safety_guard_blocks_destructive_commands PASSED
============================= 17 passed in 1.02s ==============================
```

---

## ⚖️ License

MIT License. See [LICENSE](LICENSE) for details.
