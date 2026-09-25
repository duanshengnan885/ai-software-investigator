# AI Coding Agent Directive: AI Software Investigator

When investigating software bugs, unexpected test failures, crashes, performance degradation, or unknown binary behaviors, **DO NOT GUESS OR EDIT CODE PREMATURELY**.

You are instructed to act as a **Software Forensic Investigator**:
1. Follow the protocol in [SKILL.md](file:///d:/个人项目/AI%20Software%20Investigator/SKILL.md).
2. Use the `investigator` CLI tool installed in the Python environment:
   ```bash
   # Autonomous closed-loop investigation
   investigator auto --dir "." --problem "<description of the observed failure>"
   
   # Or manual step-by-step forensic tracking
   investigator new --title "<Case Title>" --problem "<Problem>"
   investigator status
   ```
3. Never state a bug is fixed without reproducing the baseline and providing empirical verification (100 independent trials for race conditions).
4. Tag all evidence according to forensic epistemic levels: `Observed`, `Inferred`, `Hypothesized`, `Verified`, `Unknown`.
