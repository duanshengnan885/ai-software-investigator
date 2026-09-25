# AI Software Investigator: System Architecture

## 1. Architectural Philosophy

Traditional AI coding assistants guess bug causes by prompting large language models directly on source code. This approach leads to hallucinations, false confidence, and superficial fixes.

**AI Software Investigator (ASI)** is architected as an empirical forensic state machine:

```text
               +-----------------------------+
               |     Target Software /       |
               |     Mystery Executable      |
               +--------------+--------------+
                              |
                              v
                  [ Directory / Process Sandbox ]
                              |
+-----------------------------+-----------------------------+
|                FORENSIC INVESTIGATION CORE                |
|                                                           |
|  +--------------------+             +------------------+  |
|  | Hypothesis Manager | <---------+ |  Evidence Ledger |  |
|  +---------+----------+             +--------+---------+  |
|            |                                 ^            |
|            v                                 |            |
|  +--------------------+             +--------+---------+  |
|  | Experiment Planner | ----------> | Experiment Engine|  |
|  +--------------------+             +------------------+  |
|                                                           |
|  +--------------------+             +------------------+  |
|  | Diff Reasoning     | ----------> | Verification     |  |
|  | (Minimal Fix)      |             | (100 Runs Stat)  |  |
|  +--------------------+             +------------------+  |
|                                                           |
|  +-----------------------------------------------------+  |
|  | Empirical Confidence Engine & Forensic Report Gen   |  |
|  +-----------------------------------------------------+  |
+-----------------------------------------------------------+
                              |
                              v
                   [ .investigation/ State ]
```

---

## 2. Core Subsystems

### 2.1 State & Persistence Layer (`src/investigator/engine/state.py`)
All investigation state is written directly into `.investigation/`:
- `case.json`: Metadata, title, category, status, verdict, root cause link, confidence score.
- `evidence.jsonl`: Append-only ledger of verified facts, measurements, and observations.
- `hypotheses.json`: Full register of hypotheses with transitions, supporting and contradicting evidence lists.
- `experiments.jsonl`: Immutable log of executed empirical trials, commands, inputs, predictions, and metrics.
- `timeline.jsonl`: Audit trail of lifecycle milestone events.
- `findings.md`: Running forensic notebook.
- `artifacts/`: Stdout logs, stderr dumps, core dumps, memory profiles, diff files.

### 2.2 Forensic Evidence Ledger (`src/investigator/evidence/`)
Enforces the **Evidence-First Rule**. Every deduction must map back to an Evidence ID (`E-001`).
Each record is tagged with an epistemological status:
- `Observed`: Directly witnessed stdout, exit code, metric.
- `Inferred`: Logically deduced from observed evidence.
- `Hypothesized`: Mechanistic theory awaiting empirical validation.
- `Verified`: Proven through controlled experiment or fix elimination.
- `Unknown`: Ambiguous or unconfirmed data.

### 2.3 Hypothesis State Machine (`src/investigator/hypotheses/`)
Tracks hypotheses through falsifiable states:
`UNTESTED` $\to$ `PLAUSIBLE` $\to$ `SUPPORTED` / `WEAKENED` $\to$ `REJECTED` / `CONFIRMED`.
Integrity guardrails:
- Prohibits marking `CONFIRMED` if contradictory evidence is present or supporting evidence is missing.
- Prohibits marking `REJECTED` without an empirical experiment or evidence record.

### 2.4 Experiment Execution Engine (`src/investigator/experiments/`)
- `ExperimentRunner`: Executes commands with timeouts, memory tracking, and artifact preservation.
- `run_statistical()`: Repeats non-deterministic commands $N$ times to compute failure probabilities.
- `BlackboxInvestigator`: Automates binary search over input lengths and values to pinpoint discrete failure boundaries (e.g. 128 bytes OK $\to$ 129 bytes CRASH).
- `ExperimentPlanner`: Implements **Information Gain First** ranking:
  $$\text{Priority} = \frac{\text{Information Gain}}{\text{Cost} \times \text{Risk}}$$

### 2.5 Sandbox & Guardrails (`src/investigator/sandbox/`)
- `DirectorySandbox`: Clones project into an isolated workspace with snapshot and rollback capabilities.
- `GitWorktreeSandbox`: Detached worktree isolation for git projects.
- `SafetyGuard`: Blocks catastrophic commands (`rm -rf /`, `del C:\Windows`, format drives, credential theft).

### 2.6 Diff-based Reasoning & Minimal Fix (`src/investigator/reporting/diff_analyzer.py`)
- Generates unified diffs between pre-fix snapshots and post-fix files.
- Evaluates line deltas and blast radius (`LOW`, `MEDIUM`, `HIGH`).
- Enforces surgical precision over massive refactors.

### 2.7 Empirical Confidence Calculator (`src/investigator/engine/confidence.py`)
Calculates confidence using rule-based empirical factors:
- Baseline reproduction verified (+0.20)
- High-reliability empirical evidence (+0.20)
- Multi-experiment confirmation (+0.15)
- Elimination of competing hypotheses (+0.15)
- Post-fix verification zero failure rate (+0.20)
- Regression test safety (+0.10)
- Penalties for unrefuted contradictions (-0.35)
Score maps to categorical levels:
- `HIGH`: $\ge 85\%$
- `MEDIUM`: $60\% - 84\%$
- `LOW`: $< 60\%$
