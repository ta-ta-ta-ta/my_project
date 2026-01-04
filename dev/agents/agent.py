#!/usr/bin/env python3
"""Agent scaffold with optional LLM patch generation and PR creation.

Usage examples:
  # Dry run: generate patch suggestion from LLM, don't apply
  python dev/agents/agent.py --task "Implement greet i18n" --use-llm

  # Apply generated patch, run tests, create branch and commit
  python dev/agents/agent.py --task "Implement greet i18n" --use-llm --apply --push --pr

Environment variables:
  LLM_API_KEY   - API key for LLM provider (OpenAI compatible)
  LLM_PROVIDER  - provider name, default 'openai'
  GITHUB_TOKEN  - token to create PRs (repo scope)
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error
from typing import Optional


def run(cmd, **kwargs):
    print("$", " ".join(cmd))
    return subprocess.run(cmd, check=False, text=True, **kwargs)


def run_tests() -> bool:
    """Run tests in a controlled environment.

    Honors the environment variable `SKIP_TESTS` (if set to '1' or 'true').
    Creates a local `.tmp_tests` directory and sets `TMP`, `TEMP`, `TMPDIR`
    so pytest/atomicwrites uses a repo-local temporary directory to avoid
    system-wide permission issues.
    """
    skip = os.environ.get("SKIP_TESTS", "0").lower() in ("1", "true", "yes")
    if skip:
        print("SKIP_TESTS set; skipping tests.")
        return True
    print("Running tests...")
    try:
        tmpdir = os.path.join(os.getcwd(), ".tmp_tests")
        os.makedirs(tmpdir, exist_ok=True)
        env = os.environ.copy()
        env.update({"TMP": tmpdir, "TEMP": tmpdir, "TMPDIR": tmpdir})
        res = run([sys.executable, "-m", "pytest", "-q"], env=env)
        return res.returncode == 0
    except Exception as e:
        print("Error while running tests:", e)
        return False


def git(cmd):
    return run(["git"] + cmd)


def create_branch(name):
    git(["checkout", "-b", name])


def commit_all(message):
    git(["add", "-A"])
    git(["commit", "-m", message])


def get_repo_remote() -> Optional[str]:
    try:
        out = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
        return out
    except Exception:
        return None


def parse_github_repo(remote_url: str) -> Optional[tuple]:
    # supports git@github.com:owner/repo.git and https://github.com/owner/repo.git
    if remote_url.startswith("git@"):
        _, path = remote_url.split(":", 1)
    elif remote_url.startswith("http"):
        path = remote_url.rsplit("/", 2)[-2] + "/" + remote_url.rsplit("/", 1)[-1]
    else:
        path = remote_url
    path = path.removeprefix("/")
    if path.endswith(".git"):
        path = path[: -4]
    if "/" in path:
        owner, repo = path.split("/", 1)
        return owner, repo
    return None


def call_openai_chat(prompt: str, model: str = "gpt-4o") -> str:
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        raise RuntimeError("LLM_API_KEY not set")
    url = "https://api.openai.com/v1/chat/completions"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            text = resp.read().decode("utf-8")
            j = json.loads(text)
            return j["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"LLM request failed: {e.read().decode()}")


def call_cli_llm(prompt: str, cmd: str, timeout: int = 60) -> str:
    """Call a generic LLM CLI tool. The command should read prompt from stdin and write response to stdout.

    Example: set `LLM_CLI_COMMAND='github-copilot-cli --chat'` (depends on local tool).
    For gh copilot: use special handler since it doesn't accept stdin.
    """
    if not cmd:
        raise RuntimeError("LLM_CLI_COMMAND not set for CLI provider")
    
    # Special handling for gh copilot which doesn't read stdin
    if 'gh copilot' in cmd.lower() or 'gh.exe copilot' in cmd.lower():
        return call_gh_copilot(prompt, timeout=timeout)
    
    # Use shell to allow complex commands; pass prompt via stdin
    try:
        proc = subprocess.run(cmd, input=prompt, text=True, shell=True, capture_output=True, timeout=timeout)
        if proc.returncode != 0:
            raise RuntimeError(f"LLM CLI failed: {proc.stderr.strip()}")
        return proc.stdout
    except subprocess.TimeoutExpired:
        raise RuntimeError("LLM CLI command timed out")


def call_gh_copilot(prompt: str, timeout: int = 60) -> str:
    """Call gh copilot suggest using a temporary file for the prompt."""
    import tempfile
    gh_path = os.environ.get("GH_PATH", "gh")
    if not os.path.exists(gh_path) and gh_path == "gh":
        # Try default installation path on Windows
        default_gh = r"C:\Program Files\GitHub CLI\gh.exe"
        if os.path.exists(default_gh):
            gh_path = default_gh
    
    # Write prompt to temp file and use gh copilot suggest
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
        f.write(prompt)
        temp_path = f.name
    
    try:
        # Use gh copilot suggest with the prompt as argument
        # Note: gh copilot is interactive, so we use suggest -t shell as a workaround
        cmd = [gh_path, 'copilot', 'suggest', '-t', 'shell', prompt[:200]]  # truncate for safety
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        os.unlink(temp_path)
        
        if proc.returncode != 0:
            raise RuntimeError(f"gh copilot failed: {proc.stderr}")
        return proc.stdout
    except subprocess.TimeoutExpired:
        os.unlink(temp_path)
        raise RuntimeError("gh copilot timed out")
    except Exception as e:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def call_vscode_chat(prompt: str, timeout: int = 120) -> str:
    """Call VS Code Copilot Chat via a helper script.
    
    Requires:
    - GitHub Copilot subscription (Individual/Business/Enterprise)
    - VS Code with GitHub Copilot extension installed
    - User must be signed in to GitHub Copilot in VS Code
    - VSCODE_COPILOT_HELPER environment variable pointing to a bridge script
    
    This writes the prompt to a temp file and calls a helper script
    that uses the VS Code Copilot Chat API and writes the result to an output file.
    """
    import tempfile
    
    # Create temp files for input prompt and output
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_prompt.txt', encoding='utf-8') as f:
        f.write(prompt)
        prompt_file = f.name
    
    output_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_output.txt', encoding='utf-8')
    output_file.close()
    output_path = output_file.name
    
    # VS Code command to invoke Copilot Chat (user must configure this)
    vscode_helper = os.environ.get("VSCODE_COPILOT_HELPER", None)
    
    if not vscode_helper:
        # Fallback: inform user to set up VS Code integration
        os.unlink(prompt_file)
        os.unlink(output_path)
        raise RuntimeError(
            "VS Code Copilot Chat integration not configured. "
            "Please set VSCODE_COPILOT_HELPER to a script that reads from prompt file and writes to output file, "
            "or use 'openai' provider with API key instead."
        )
    
    try:
        # Call the helper script: it should read prompt_file and write to output_path
        cmd = [vscode_helper, prompt_file, output_path]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        
        if proc.returncode != 0:
            raise RuntimeError(f"VS Code Copilot helper failed: {proc.stderr}")
        
        # Read the output
        with open(output_path, 'r', encoding='utf-8') as f:
            result = f.read()
        
        os.unlink(prompt_file)
        os.unlink(output_path)
        return result
    except subprocess.TimeoutExpired:
        os.unlink(prompt_file)
        os.unlink(output_path)
        raise RuntimeError("VS Code Copilot helper timed out")
    except Exception as e:
        if os.path.exists(prompt_file):
            os.unlink(prompt_file)
        if os.path.exists(output_path):
            os.unlink(output_path)
        raise


def call_llm(prompt: str, provider: str = "openai") -> str:
    provider = (provider or os.environ.get("LLM_PROVIDER", "openai")).lower()
    if provider in ("openai", "openai_api"):
        model = os.environ.get("LLM_MODEL", "gpt-4o")
        return call_openai_chat(prompt, model=model)
    # VS Code Copilot Chat API (requires Copilot subscription)
    if provider in ("vscode", "vscode_chat", "vscode_copilot"):
        return call_vscode_chat(prompt)
    # GitHub Copilot CLI provider
    if provider in ("copilot", "copilot_cli", "gh_copilot"):
        return call_gh_copilot(prompt)
    # generic CLI-based provider (other local tools)
    if provider == "cli":
        cmd = os.environ.get("LLM_CLI_COMMAND")
        return call_cli_llm(prompt, cmd=cmd)
    raise RuntimeError(f"Unknown LLM provider: {provider}")


def request_patch_from_llm(task: str) -> Optional[str]:
    prompt = (
        "You are given a Git repository and a concise task. Produce a unified diff patch"
        " (git format-patch style) that implements the task. Only output the patch between"
        " the markers PATCH_START and PATCH_END. If no changes are needed, output PATCH_START\nPATCH_END."
        f"\n\nTask:\n{task}\n\nRepository files: list the important files and tests and any failing test output if available."
    )
    print("Requesting patch from LLM...")
    provider = os.environ.get("LLM_PROVIDER", "openai").lower()
    try:
        content = call_llm(prompt, provider=provider)
    except Exception as e:
        raise
    # Extract between markers
    start = content.find("PATCH_START")
    end = content.find("PATCH_END")
    if start != -1 and end != -1 and end > start:
        patch = content[start + len("PATCH_START") : end].strip()
        return patch
    # fallback: return whole content if it looks like a diff
    if content.strip().startswith("diff --git") or content.strip().startswith("--- a/"):
        return content
    return None


def apply_patch(patch_text: str) -> bool:
    if not patch_text:
        print("No patch to apply")
        return False
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".patch") as fh:
        fh.write(patch_text)
        patch_path = fh.name
    print("Applying patch:", patch_path)
    res = run(["git", "apply", "--index", patch_path])
    return res.returncode == 0


def create_github_pr(branch: str, title: str, body: str) -> Optional[str]:
    remote = get_repo_remote()
    if not remote:
        print("Could not determine git remote; skipping PR creation")
        return None
    repo = parse_github_repo(remote)
    if not repo:
        print("Could not parse repo from remote; skipping PR creation")
        return None
    owner, repo_name = repo
    url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN not set; cannot create PR")
        return None
    body_json = json.dumps({"title": title, "head": branch, "base": "main", "body": body}).encode("utf-8")
    req = urllib.request.Request(url, data=body_json, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"token {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            j = json.loads(resp.read().decode())
            pr_url = j.get("html_url")
            print("Created PR:", pr_url)
            return pr_url
    except urllib.error.HTTPError as e:
        print("Failed to create PR:", e.read().decode())
        return None


def main():
    p = argparse.ArgumentParser(description="Agent scaffold with LLM and PR support")
    p.add_argument("--task", required=True, help="Short task description")
    p.add_argument("--apply", action="store_true", help="Apply patch and commit locally")
    p.add_argument("--use-llm", action="store_true", help="Use LLM to generate patch suggestion")
    p.add_argument("--push", action="store_true", help="Push branch to origin after commit")
    p.add_argument("--pr", action="store_true", help="Create a GitHub PR after push (requires GITHUB_TOKEN)")
    p.add_argument("--skip-tests", action="store_true", help="Skip running tests (also honored via SKIP_TESTS=1)")
    args = p.parse_args()

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    branch = f"agent/{timestamp}"

    print("Task:", args.task)

    patch_text = None
    if args.use_llm:
        try:
            patch_text = request_patch_from_llm(args.task)
        except Exception as e:
            print("LLM call failed:", e)

    # honor --skip-tests flag by setting env var used by run_tests
    if args.skip_tests:
        os.environ["SKIP_TESTS"] = "1"

    if patch_text:
        print("LLM returned a patch (length=%d)" % len(patch_text))
        if args.apply:
            create_branch(branch)
            ok = apply_patch(patch_text)
            if not ok:
                print("git apply failed; aborting")
                return
            commit_all(f"agent: implement - {args.task}")
            if args.push:
                git(["push", "-u", "origin", branch])
            tests_ok = run_tests()
            if tests_ok:
                print("Tests passed after applying patch")
                if args.pr and args.push:
                    create_github_pr(branch, f"agent: {args.task}", "Automated PR created by agent")
            else:
                print("Tests failed after applying patch; please inspect changes.")
        else:
            print("Patch (dry-run):\n")
            print(patch_text)
    else:
        print("No patch produced by LLM or LLM not used. Running tests only.")
        ok = run_tests()
        print("Tests passing:", ok)


if __name__ == "__main__":
    main()
