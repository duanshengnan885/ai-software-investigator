# Investigation Practical Guide

This guide explains how to investigate the four primary defect categories using AI Software Investigator.

---

## 1. Ordinary Bug (Crash, Exception, Logic Bug)

### Scenario
An API endpoint or script crashes on certain inputs (e.g. `order_processor.py 10`).

### Investigation Workflow
1. **Intake & Discovery:**
   Register case with category `bug`. Capture Python version, dependencies, OS.
2. **Reproduction:**
   Execute `python order_processor.py 10`. Record exit code and stack trace in `evidence.jsonl`.
3. **Hypotheses:**
   - `H1`: External dependency failure (database or network).
   - `H2`: Boundary off-by-one error on discount tier threshold lookup.
   - `H3`: Float precision underflow.
4. **Controlled Experiments:**
   - Test below boundary: `python order_processor.py 9` $\to$ Exit 0.
   - Test above boundary: `python order_processor.py 11` $\to$ Exit 0.
   - Test isolated float arithmetic: `python order_processor.py 5` $\to$ Exit 0.
5. **Elimination:**
   Eliminate H1 and H3 based on clean execution of inputs 5, 9, 11.
6. **Minimal Fix:**
   Change `>` to `>=` in the boundary comparison. Blast radius: LOW (+1 / -1 lines).
7. **Verification:**
   Run full regression suite across all tier intervals (1, 9, 10, 11, 49, 50, 51).

---

## 2. Intermittent & Concurrency Bug (Race Condition, Deadlock)

### Scenario
A multi-threaded cache or worker pool crashes randomly ~20% of the time under concurrent load.

### Investigation Workflow
1. **Baseline Statistical Repro:**
   Do NOT run once! Run 30-50 iterations using `engine.reproduce_problem(runs=30)`. Establish baseline failure rate (e.g. 23.3%).
2. **Hypotheses:**
   - `H1`: Memory leak / OOM killer.
   - `H2`: Unsynchronized dictionary mutation in critical section.
   - `H3`: OS thread allocation failure.
3. **Concurrency Sweep Experiments:**
   - 1 Thread (20 runs): Expected 0% failure $\to$ Observed: 0% failure.
   - 4 Threads (20 runs): Expected moderate failure $\to$ Observed: 15% failure.
   - 16 Threads (20 runs): Expected high failure $\to$ Observed: 45% failure.
   - Failure probability strictly scales with concurrency factor $\to$ Confirms H2.
4. **Eliminate Alternatives:**
   Profile process memory heap over 100 iterations $\to$ Heap stable at 25MB $\to$ Eliminates H1.
5. **Minimal Fix:**
   Introduce `threading.Lock()` protecting dictionary insertion and pruning.
6. **Statistical Verification:**
   Execute 100 consecutive runs with 16 worker threads. Must observe 0 failures across 100 trials!

---

## 3. Black-Box Investigation (No Source Code Available)

### Scenario
A closed-source compiled binary `mystery_parser.exe` crashes with SIGSEGV on certain inputs.

### Investigation Workflow
1. **Intake:**
   Category `blackbox`.
2. **Baseline Observation:**
   - `mystery_parser hello` $\to$ Exit 0 (OK)
   - `mystery_parser [300-char string]` $\to$ Exit 139 (SIGSEGV CRASH)
3. **Binary Search Boundary Discovery:**
   Execute automated binary search over length range $1 \to 512$:
   - Len 1: OK
   - Len 512: CRASH
   - Len 256: CRASH
   - Len 128: OK
   - Len 192: CRASH
   - Len 130: CRASH
   - Len 129: CRASH
   - Discovers exact boundary: **128 (OK) $\to$ 129 (CRASH)**!
4. **Character Set Fuzzing:**
   Test length 128 with ASCII, Unicode, special symbols, punctuation. All pass cleanly. Proves crash is independent of characters and strictly bound to length.
5. **Root Cause Deduction:**
   128-byte static stack buffer overflow.
6. **Report:**
   Generate specification document with input boundary constraints.
