#!/usr/bin/env python3
"""Simple local "agent" script to run tests and create a branch with a patch.

This is an example scaffold — it does NOT call Copilot. To use an LLM,
configure `LLM_PROVIDER` / `LLM_API_KEY` in your environment and extend this script.
"""
import argparse
import datetime
import os
import subprocess
import sys


def run(cmd, **kwargs):
    print("$", " ".join(cmd))
    return subprocess.run(cmd, check=False, text=True, **kwargs)


def run_tests():
    print("Running tests...")
    res = run([sys.executable, "-m", "pytest", "-q"])
    return res.returncode == 0


def git(cmd):
    return run(["git"] + cmd)


def create_branch(name):
    git(["checkout", "-b", name])


def commit_all(message):
    git(["add", "-A"])
    git(["commit", "-m", message])


def main():
    p = argparse.ArgumentParser(description="Simple local agent scaffold")
    p.add_argument("--task", required=True, help="Short task description")
    p.add_argument("--apply", action="store_true", help="Actually create branch and commit (default: dry-run)")
    args = p.parse_args()

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    branch = f"agent/{timestamp}"

    print("Task:", args.task)
    ok = run_tests()
    print("Tests passing:", ok)

    patch_file = os.path.join("dev", "agents", f"agent_patch_{timestamp}.txt")
    with open(patch_file, "w", encoding="utf-8") as fh:
        fh.write(f"# Agent task: {args.task}\n")
        fh.write("# Tests passing: %s\n" % ok)
        fh.write("# Next steps: run tests, implement changes, add tests, commit, push, open PR\n")

    print("Wrote patch note:", patch_file)

    if args.apply:
        create_branch(branch)
        commit_all(f"agent: start task - {args.task}")
        print("Created branch:", branch)
        print("Now push and open a PR, or continue implementing locally.")
    else:
        print("Dry run: use --apply to create branch and commit locally.")


if __name__ == "__main__":
    main()
