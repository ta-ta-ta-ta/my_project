#!/usr/bin/env python3
"""Multi-persona orchestrator: load personas and run agent loop.

Usage:
  python dev/agents/auto_develop.py --task "Describe feature" --dry-run --use-llm

This script imports helper functions from `agent.py` in the same folder and
invokes the LLM for each persona defined in `personas.json`.
"""
import argparse
import json
import os
import importlib.util
import datetime
from typing import Optional

HERE = os.path.dirname(__file__)
AGENT_PY = os.path.join(HERE, "agent.py")

spec = importlib.util.spec_from_file_location("agent_mod", AGENT_PY)
agent_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_mod)

PERSONAS_PATH = os.path.join(HERE, "personas.json")


def load_personas(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        j = json.load(fh)
    return j.get("personas", [])


def timestamp():
    return datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")


def run_loop(task: str, use_llm: bool, apply: bool, push: bool, pr: bool, dry_run: bool):
    personas = load_personas(PERSONAS_PATH)
    last_branch: Optional[str] = None
    for p in personas:
        pid = p.get("id")
        name = p.get("name")
        role = p.get("role_prompt")
        print(f"\n=== Persona: {pid} ({name}) ===")
        prompt = f"{role}\n\nTask:\n{task}\n\nRespond with a git-format unified diff between PATCH_START and PATCH_END."
        patch = None
        if use_llm:
            try:
                patch = agent_mod.request_patch_from_llm(prompt)
            except Exception as e:
                print(f"[{pid}] LLM error: {e}")
        if not patch:
            print(f"[{pid}] No patch produced.")
            continue
        print(f"[{pid}] Patch length: {len(patch)}")
        if dry_run or not apply:
            print(f"[{pid}] Dry-run patch:\n")
            print(patch)
            continue
        branch = f"agent/{pid}/{timestamp()}"
        last_branch = branch
        agent_mod.create_branch(branch)
        ok = agent_mod.apply_patch(patch)
        if not ok:
            print(f"[{pid}] git apply failed; skipping remaining steps for this persona.")
            continue
        agent_mod.commit_all(f"agent({pid}): {task}")
        if push:
            agent_mod.git(["push", "-u", "origin", branch])

    # Do not run tests during dry-run; allow caller to set SKIP_TESTS to skip tests.
    if dry_run:
        print("Dry-run mode; skipping test execution.")
        tests_ok = True
    else:
        tests_ok = agent_mod.run_tests()
    print("\nFinal test result:", tests_ok)
    if tests_ok and pr and push and last_branch:
        agent_mod.create_github_pr(last_branch, f"agent: {task}", "Automated PR created by agents")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task", required=True)
    p.add_argument("--use-llm", action="store_true")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--push", action="store_true")
    p.add_argument("--pr", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--skip-tests", action="store_true", help="Skip running tests at the end of the loop")
    args = p.parse_args()
    if args.skip_tests:
        os.environ["SKIP_TESTS"] = "1"
    run_loop(args.task, args.use_llm, args.apply, args.push, args.pr, args.dry_run)


if __name__ == "__main__":
    main()
