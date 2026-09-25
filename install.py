#!/usr/bin/env python3
"""
AI Software Investigator (ASI) - Universal Skill Installer
Installs the AI Software Investigator skill into your AI coding assistant environment:
- Google Antigravity (AGY)
- Claude Code / Claude Desktop
- OpenCode / Codex / Reasonix
- Cursor / Windsurf
- Local Workspace (.agents/skills)
"""

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SKILL_MD = REPO_ROOT / "SKILL.md"

def get_home_dir() -> Path:
    return Path.home()

def detect_platforms():
    home = get_home_dir()
    platforms = {}

    # 1. Google Antigravity
    antigravity_dir = home / ".gemini" / "config" / "skills"
    platforms["antigravity"] = {
        "name": "Google Antigravity (AGY)",
        "target": antigravity_dir / "ai-software-investigator",
        "detected": (home / ".gemini").exists(),
    }

    # 2. Claude Code
    claude_dir = home / ".claude" / "skills"
    platforms["claude"] = {
        "name": "Claude Code",
        "target": claude_dir / "ai-software-investigator",
        "detected": (home / ".claude").exists(),
    }

    # 3. OpenCode / Codex / Universal Agents
    agents_dir = home / ".agents" / "skills"
    platforms["agents"] = {
        "name": "Universal Agent Skills (~/.agents/skills)",
        "target": agents_dir / "ai-software-investigator",
        "detected": (home / ".agents").exists(),
    }

    return platforms

def copy_skill(target_dir: Path):
    target_dir.mkdir(parents=True, exist_ok=True)
    target_skill_md = target_dir / "SKILL.md"
    shutil.copy2(SKILL_MD, target_skill_md)
    print(f"  [+] Installed SKILL.md -> {target_skill_md}")

    # Optional: copy reference docs if needed
    docs_dir = REPO_ROOT / "docs"
    if docs_dir.exists():
        target_docs = target_dir / "references"
        target_docs.mkdir(parents=True, exist_ok=True)
        for doc_file in docs_dir.glob("*.md"):
            shutil.copy2(doc_file, target_docs / doc_file.name)
        print(f"  [+] Installed forensic reference docs -> {target_docs}")

def install_cursor_rule(target_workspace: Path):
    rules_dir = target_workspace / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    rule_file = rules_dir / "ai-software-investigator.mdc"
    
    content = f"""---
description: AI Software Investigator forensic debugging rule. Use when debugging crashes, bugs, race conditions, or black-box errors.
globs: *
alwaysApply: false
---

# AI Software Investigator Forensic Protocol

When user asks to investigate a bug, diagnose a crash, or debug an intermittent failure:
1. Do NOT guess or edit code immediately.
2. Run empirical investigation using the investigator CLI or forensic loop:
   ```bash
   investigator auto --dir . --problem "<problem description>"
   ```
3. Adhere to the Evidence-First rule: Every deduction must link to an evidence ID in `.investigation/evidence.jsonl`.
4. Statistical verification: Validate fixes over 100 runs for race conditions using Rule of Three (p <= 3/N).
"""
    rule_file.write_text(content, encoding="utf-8")
    print(f"  [+] Generated Cursor rule -> {rule_file}")

def install_python_package():
    print("\n[*] Installing 'ai-software-investigator' Python package into current environment...")
    cmd = [sys.executable, "-m", "pip", "install", "-e", str(REPO_ROOT)]
    try:
        subprocess.check_call(cmd)
        print("  [+] Successfully installed CLI tool: 'investigator'")
    except subprocess.CalledProcessError as e:
        print(f"  [!] Failed to install package: {e}. You can run 'pip install -e .' manually.", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="AI Software Investigator Skill Installer")
    parser.add_argument("--antigravity", action="store_true", help="Install into Google Antigravity (~/.gemini/config/skills/)")
    parser.add_argument("--claude", action="store_true", help="Install into Claude Code (~/.claude/skills/)")
    parser.add_argument("--agents", action="store_true", help="Install into Universal Agents root (~/.agents/skills/)")
    parser.add_argument("--workspace", type=str, help="Install into a specific workspace (.agents/skills/ in target directory)")
    parser.add_argument("--cursor", type=str, help="Install Cursor rule into specified workspace directory")
    parser.add_argument("--all", action="store_true", help="Install into all detected AI platforms")
    parser.add_argument("--skip-pip", action="store_true", help="Skip running pip install -e .")

    args = parser.parse_args()

    if not SKILL_MD.exists():
        print(f"[!] Error: SKILL.md not found at {SKILL_MD}", file=sys.stderr)
        sys.exit(1)

    platforms = detect_platforms()
    installed_count = 0

    print("============================================================")
    print("    AI Software Investigator (ASI) - Skill Installer        ")
    print("============================================================")

    # Specific flags
    if args.antigravity:
        print("\n[*] Installing into Google Antigravity...")
        copy_skill(platforms["antigravity"]["target"])
        installed_count += 1

    if args.claude:
        print("\n[*] Installing into Claude Code...")
        copy_skill(platforms["claude"]["target"])
        installed_count += 1

    if args.agents:
        print("\n[*] Installing into Universal Agents directory...")
        copy_skill(platforms["agents"]["target"])
        installed_count += 1

    if args.workspace:
        ws_path = Path(args.workspace).resolve()
        target = ws_path / ".agents" / "skills" / "ai-software-investigator"
        print(f"\n[*] Installing into workspace: {ws_path}...")
        copy_skill(target)
        installed_count += 1

    if args.cursor:
        ws_path = Path(args.cursor).resolve()
        print(f"\n[*] Installing Cursor rule into: {ws_path}...")
        install_cursor_rule(ws_path)
        installed_count += 1

    # Default / --all behavior
    if not (args.antigravity or args.claude or args.agents or args.workspace or args.cursor):
        print("\n[*] Auto-detecting installed AI assistant platforms:")
        any_detected = False
        for key, info in platforms.items():
            status = "FOUND" if info["detected"] else "NOT DETECTED"
            print(f"  - {info['name']}: {status}")
            if info["detected"] or args.all:
                any_detected = True
                print(f"    -> Installing skill to {info['target']}...")
                copy_skill(info["target"])
                installed_count += 1

        if not any_detected:
            # Fallback: install into ~/.agents/skills
            print("\n[*] No specific AI platform directory found. Installing into default universal location:")
            copy_skill(platforms["agents"]["target"])
            installed_count += 1

    if not args.skip_pip:
        install_python_package()

    print("\n============================================================")
    print(f"  Installation complete! ({installed_count} skill location(s) configured)")
    print("============================================================")
    print("\nHow to use in your AI platform (Claude Code, Antigravity, Cursor, etc.):")
    print("  1. In conversation with your AI assistant, type:")
    print("     /investigate \"The server occasionally drops connections under load\"")
    print("     or:")
    print("     \"请使用 ai-software-investigator 技能调查为什么这个脚本运行会崩溃\"")
    print("  2. In your terminal, you can run the investigator CLI directly:")
    print("     investigator auto --dir . --problem \"<problem description>\"")
    print("     investigator demo 1")
    print("============================================================\n")

if __name__ == "__main__":
    main()
