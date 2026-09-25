#!/usr/bin/env python3
"""
AI Software Investigator (ASI) - Universal Skill Installer
Installs the AI Software Investigator skill into your AI coding assistant environment:
- Google Antigravity (AGY)
- Claude Code / Claude Desktop
- OpenAI Codex / Codex CLI
- 豆包 (Doubao) / 豆包 MarsCode / Trae IDE
- DeepSeek / DeepSeek-Harness
- OpenCode / Reasonix / Universal Agents
- Cursor / Windsurf
- Local Workspace
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

    # 3. OpenAI Codex
    codex_dir = home / ".codex" / "skills"
    platforms["codex"] = {
        "name": "OpenAI Codex CLI",
        "target": codex_dir / "ai-software-investigator",
        "detected": (home / ".codex").exists(),
    }

    # 4. 豆包 / MarsCode / Trae
    doubao_dir = home / ".doubao" / "skills"
    platforms["doubao"] = {
        "name": "豆包 (Doubao) / MarsCode",
        "target": doubao_dir / "ai-software-investigator",
        "detected": (home / ".doubao").exists() or (home / ".marscode").exists() or (home / ".trae").exists(),
    }

    # 5. DeepSeek / DeepSeek-Harness
    deepseek_dir = home / ".deepseek" / "skills"
    platforms["deepseek"] = {
        "name": "DeepSeek / DeepSeek-Harness",
        "target": deepseek_dir / "ai-software-investigator",
        "detected": (home / ".deepseek").exists(),
    }

    # 6. Universal Agent Skills (~/.agents/skills)
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

    # Copy reference docs
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
    src_file = REPO_ROOT / ".cursor" / "rules" / "ai-software-investigator.mdc"
    if src_file.exists():
        shutil.copy2(src_file, rule_file)
    else:
        rule_file.write_text("# AI Software Investigator Rule", encoding="utf-8")
    print(f"  [+] Installed Cursor rule -> {rule_file}")

def install_trae_rule(target_workspace: Path):
    rules_dir = target_workspace / ".trae" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    rule_file = rules_dir / "ai-software-investigator.md"
    src_file = REPO_ROOT / ".trae" / "rules" / "ai-software-investigator.md"
    if src_file.exists():
        shutil.copy2(src_file, rule_file)
    print(f"  [+] Installed Trae IDE rule -> {rule_file}")

def install_marscode_rule(target_workspace: Path):
    rules_dir = target_workspace / ".marscode" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    rule_file = rules_dir / "ai-software-investigator.md"
    src_file = REPO_ROOT / ".marscode" / "rules" / "ai-software-investigator.md"
    if src_file.exists():
        shutil.copy2(src_file, rule_file)
    print(f"  [+] Installed MarsCode IDE rule -> {rule_file}")

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
    parser.add_argument("--codex", action="store_true", help="Install into OpenAI Codex CLI (~/.codex/skills/)")
    parser.add_argument("--doubao", action="store_true", help="Install for 豆包 / MarsCode (~/.doubao/skills/)")
    parser.add_argument("--deepseek", action="store_true", help="Install for DeepSeek / Harness (~/.deepseek/skills/)")
    parser.add_argument("--agents", action="store_true", help="Install into Universal Agents root (~/.agents/skills/)")
    parser.add_argument("--workspace", type=str, help="Install into a specific workspace (.agents/skills/ in target directory)")
    parser.add_argument("--cursor", type=str, help="Install Cursor rule into specified workspace directory")
    parser.add_argument("--trae", type=str, help="Install Trae IDE rule into specified workspace directory")
    parser.add_argument("--all", action="store_true", help="Install into all detected AI platforms")
    parser.add_argument("--skip-pip", action="store_true", help="Skip running pip install -e .")

    args = parser.parse_args()

    if not SKILL_MD.exists():
        print(f"[!] Error: SKILL.md not found at {SKILL_MD}", file=sys.stderr)
        sys.exit(1)

    platforms = detect_platforms()
    installed_count = 0

    print("============================================================")
    print("    AI Software Investigator (ASI) - Multi-Agent Installer  ")
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

    if args.codex:
        print("\n[*] Installing into OpenAI Codex...")
        copy_skill(platforms["codex"]["target"])
        installed_count += 1

    if args.doubao:
        print("\n[*] Installing for 豆包 (Doubao)...")
        copy_skill(platforms["doubao"]["target"])
        installed_count += 1

    if args.deepseek:
        print("\n[*] Installing for DeepSeek / DeepSeek-Harness...")
        copy_skill(platforms["deepseek"]["target"])
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
        # Also copy agent constitution files
        for f_name in ["AGENTS.md", "CODEX.md", "DOUBAO.md", "DEEPSEEK.md"]:
            src = REPO_ROOT / f_name
            if src.exists():
                shutil.copy2(src, ws_path / f_name)
                print(f"  [+] Installed directive -> {ws_path / f_name}")
        installed_count += 1

    if args.cursor:
        ws_path = Path(args.cursor).resolve()
        print(f"\n[*] Installing Cursor rule into: {ws_path}...")
        install_cursor_rule(ws_path)
        installed_count += 1

    if args.trae:
        ws_path = Path(args.trae).resolve()
        print(f"\n[*] Installing Trae / MarsCode rules into: {ws_path}...")
        install_trae_rule(ws_path)
        install_marscode_rule(ws_path)
        installed_count += 1

    # Default / --all auto-detect behavior
    has_specific = any([
        args.antigravity, args.claude, args.codex, args.doubao,
        args.deepseek, args.agents, args.workspace, args.cursor, args.trae
    ])

    if not has_specific:
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
    print("\nSupported Platforms & Usage:")
    print("  • Google Antigravity: /investigate \"...\"")
    print("  • Claude Code:        /investigate \"...\"")
    print("  • OpenAI Codex:       Follows CODEX.md & calls 'investigator auto'")
    print("  • 豆包 / Trae:        Follows DOUBAO.md & .trae/rules/")
    print("  • DeepSeek / Harness: investigator auto --provider deepseek --model deepseek-reasoner")
    print("                        investigator harness --spec task.json")
    print("============================================================\n")

if __name__ == "__main__":
    main()
