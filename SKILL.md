---
name: ai-software-investigator
description: Autonomous software forensic investigation engine. Use when investigating software bugs, crashes, intermittent race conditions, memory leaks, performance bottlenecks, or closed/black-box binary behaviors before writing fixes.
---

# AI Software Investigator (ASI)

> **Forensic Mandate:**
> Do NOT guess why a bug occurs or jump directly to code modification.
> Function like a software forensic pathologist:
> Formulate Hypotheses → Design Empirical Experiments → Execute in Sandbox → Collect Evidence → Eliminate Hypotheses → Identify Root Cause → Minimal Surgical Fix → Independent Verification.

---

## 1. Purpose

AI Software Investigator (ASI) provides an autonomous, evidence-first, hypothesis-driven forensic methodology to diagnose and resolve software defects, intermittent reliability failures, performance bottlenecks, and closed-box unknown behaviors.

The core philosophy is:
**"Give it a broken or unknown program. Let it investigate before it fixes."**

---

## 2. When to Activate

Activate this skill whenever:
- A user reports a crash, exception, hang, logic flaw, or incorrect behavior.
- A failure is intermittent, non-deterministic, flaky, or load-dependent.
- A system suffers from memory leaks, CPU spikes, or latency degradation.
- A user provides a compiled, closed-source, or mystery binary/script without source code ("Investigate why this program crashes on certain inputs").
- The root cause is unknown or contested, and claims must be substantiated with verifiable evidence rather than speculative guesses.

**Trigger Keywords:**
`/investigate`, `/diagnose`, `排查问题`, `调查崩溃`, `定位Root Cause`, `软件法医`, `间歇性Bug`, `黑盒测试`, `找出崩溃原因`, `内存泄漏调查`.

---

## 3. Investigation Protocol (The 12-Step Forensic Loop)

```text
[1] Project Intake & Case Registration
      ↓
[2] Environment Discovery
      ↓
[3] Evidence Collection & Baseline Reproduction
      ↓
[4] Falsifiable Hypothesis Formulation
      ↓
[5] Information-Gain-First Experiment Planning
      ↓
[6] Controlled Sandbox Execution
      ↓
[7] Evidence Analysis & Anti-Hallucination Claim Tagging
      ↓
[8] Hypothesis Elimination & Refutation
      ↓
[9] Root Cause Identification (What, Why, Where, How Confirmed)
      ↓
[10] Minimal Surgical Fix & Diff Blast Radius Analysis
      ↓
[11] Independent & Statistical Verification (e.g. 100 runs)
      ↓
[12] Forensic Report Generation & Closed State
```

---

## 4. Anti-Hallucination & Evidence Rules (STRICT)

1. **Evidence First Rule:**
   - Every claim, deduction, or conclusion MUST be bound to a specific evidence ID (`E-001`, `E-002`, etc.) in `.investigation/evidence.jsonl`.
   - Never write "tests show..." without an `EXP-xxx` experiment record.
   - Never write "logs indicate..." without an excerpt or artifact reference.
   - Never write "the bug is confirmed" without reproducing the baseline failure.

2. **Epistemological Status Labeling:**
   Every piece of evidence and finding must be explicitly tagged as one of:
   - `Observed`: Directly recorded stdout, stderr, exit code, or profile metric.
   - `Inferred`: Logically deduced from observed evidence.
   - `Hypothesized`: Proposed mechanistic explanation awaiting empirical test.
   - `Verified`: Proven through controlled experiment or fix elimination.
   - `Unknown`: Ambiguous or unconfirmed data point.

3. **No Fake Confidence Rule & Binomial Confidence Bounds:**
   - Confidence scores must NEVER be arbitrarily guessed. They must be mathematically derived via `ConfidenceCalculator`:
     - Baseline reproduction established (+0.20)
     - Confirmed hypothesis supported by independent high-reliability evidence (+0.20)
     - Tested across $\ge 2$ empirical experiments (+0.15)
     - Systematic elimination of competing hypotheses (+0.15)
     - Post-fix verification demonstrates 0 failures (+0.20)
     - Regression suite passes (+0.10)
     - Unexplained contradictory evidence penalty (-0.35)
   - **Binomial Confidence Interval:** For zero-failure post-fix trials ($k = 0$ in $N$ runs), report the **Rule of Three** bound:
     $$\text{True failure probability } p \le \frac{3}{N} \text{ at } 95\% \text{ statistical confidence.}$$
     Never claim "Bug fixed with 100% certainty"; state exact empirical trials and statistical upper bounds.

---

## 5. Hypothesis Rules

1. **Explicit Tracking:**
   Every hypothesis is tracked in `.investigation/hypotheses.json` with an ID (`H1`, `H2`, ...).
2. **Mandatory Lifecycle States:**
   - `UNTESTED`: Registered, awaiting test.
   - `PLAUSIBLE`: Consistent with initial facts, pending controlled separation.
   - `SUPPORTED`: Direct experiment prediction matched observation.
   - `WEAKENED`: Evidence partially contradicts or lacks correlation.
   - `REJECTED`: Falsified by controlled experiment or contradicting evidence.
   - `CONFIRMED`: Irrefutably validated with causal proof.
3. **Forensic Integrity Guardrails:**
   - **PROHIBITED:** Transitioning to `CONFIRMED` while any contradictory evidence remains unrefuted.
   - **PROHIBITED:** Transitioning to `CONFIRMED` without verified supporting evidence.
   - **PROHIBITED:** Transitioning to `REJECTED` without an empirical experiment or evidence record.

---

## 6. Experiment Rules (Information Gain First)

When designing experiments, prioritize them according to:
$$\text{Priority Score} = \frac{\text{Information Gain}}{\text{Cost} \times \text{Risk}}$$

1. **Prediction Before Execution:**
   Every experiment (`EXP-xxx`) must document:
   - Objective: What question does this answer?
   - Target Hypothesis: Which hypothesis is on trial?
   - Expected Prediction: If $H$ is true, what will be observed? If false, what will be observed?
2. **Concurrency Sweeps for Intermittent Bugs:**
   Never assume a failure is "random". Sweep concurrency (1 thread $\to$ 4 threads $\to$ 16 threads) or load to test race conditions.
3. **Black-box Boundary Search:**
   When investigating unknown binaries without source code:
   - Use binary search over input lengths ($1 \to 512$) to isolate the exact boundary (e.g. 128 OK $\to$ 129 CRASH).
   - Use character invariance fuzzing (digits, symbols, punctuation, unicode, format strings) to eliminate semantic or character-set hypotheses.

---

## 7. Sandbox & Safety Rules

1. **Filesystem Isolation:**
   - When modifying source code or running tests that write to disk, operate in an isolated workspace (Git worktree or temporary directory sandbox).
   - Take snapshots before applying patches so changes can be cleanly rolled back.
2. **Destructive Command Interception:**
   - Destructive operations (`rm -rf`, `del /f /s /q`, formatting disks, accessing `.env` or credentials) are blocked by `SafetyGuard` and require explicit human approval.

---

## 8. Minimal Fix Strategy

1. **Surgical Precision:**
   - Prioritize the smallest possible patch that eliminates the root cause with zero side effects.
   - Prefer bounds checks, lock acquisition, or off-by-one correction over architectural rewrites.
2. **Diff-based Reasoning:**
   - Evaluate Before vs After for each modified file.
   - Document lines added, lines removed, and explicit rationale per file.
   - If blast radius is HIGH (>3 files or >50 lines), provide explicit architectural justification.

---

## 9. Independent & Statistical Verification

1. **Deterministic Bugs:**
   - Rerun original reproduction vector $\ge 5$ times. Must yield 0 failures.
   - Run complete regression suite.
2. **Intermittent / Probabilistic Bugs:**
   - Rerun reproduction vector $\ge 100$ times under stress/concurrency.
   - Quantify failure rate: must achieve $0.0\%$ failure rate.
   - Document clearly: *"Empirically validated with 100 runs; 0 reproductions observed."*

---

## 10. Termination Conditions

Investigations must terminate cleanly under one of four explicit verdicts:

1. **`SUCCESS`**:
   Root Cause definitively identified + Minimal Fix applied + Independent Verification passed (0 failures) + Regression suite passed.
2. **`PARTIAL`**:
   Root Cause identified with high empirical confidence, but full fix or end-to-end verification cannot be applied (e.g. read-only environment or black-box binary).
3. **`BLOCKED`**:
   Investigation halted due to missing dependencies, unexecutable reproduction harness, or denied permissions.
4. **`UNKNOWN`**:
   Exhaustive experiments failed to reproduce or isolate the defect. AI terminates honestly rather than fabricating a conclusion.

---

## 11. Command Reference

```bash
# Launch autonomous closed-loop AI investigation (No human-in-the-loop needed)
investigator auto --problem "Program intermittently crashes under concurrent load" --dir "."

# Initialize a new investigation case manually
investigator new --title "Cache Crash" --problem "Intermittent crash under load" --dir "."

# View live investigation status board
investigator status --dir "."

# Execute automated black-box boundary discovery on a binary
investigator blackbox --cmd "python mystery_parser.py {input}" --min-len 1 --max-len 512

# Run automated demonstrations
investigator demo 1   # Ordinary Logic Bug
investigator demo 2   # Intermittent Race Condition (100-run verification)
investigator demo 3   # Black-box Binary Boundary Investigation
```
