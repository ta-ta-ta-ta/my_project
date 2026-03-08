# CLAUDE.md

This file provides guidance for AI assistants working in this repository.

## Project Overview

`my-project` is a Python scaffold demonstrating AI-assisted development workflows. It integrates LLM-based code generation (OpenAI/GPT-4o-mini) with GitHub Actions CI/CD for automated patch generation, testing, and pull request creation.

## Repository Structure

```
my_project/
├── .github/
│   ├── copilot-instructions.md   # Coding standards and conventions
│   └── workflows/
│       ├── agent.yml             # Dispatch workflow: LLM generates code → auto-commit
│       └── agent-ci.yml          # CI + optional LLM agent run on push/PR
├── dev/
│   └── agents/
│       ├── agent.py              # Core agent: test runner, LLM patch generator, PR creator
│       ├── config.example.toml   # Example config (copy to config.toml, not committed)
│       └── README.md             # Agent usage documentation
├── main.py                       # Entry point (prints hello message)
├── generated_code.py             # Output file for LLM-generated code
├── pyproject.toml                # Project metadata and dependencies
└── uv.lock                       # Locked dependency versions
```

## Development Setup

This project uses [uv](https://github.com/astral-sh/uv) as the package manager.

```bash
# Install dependencies
uv sync

# Run the project
python main.py
```

## Running Tests

```bash
python -m pytest -q
```

Tests should live in a `tests/` directory. Currently no test files exist — add new tests there when implementing features.

## Agent Scaffold

`dev/agents/agent.py` is the main automation tool. It can:
- Run tests locally
- Request an LLM to generate a patch for a task
- Apply that patch and commit
- Push to origin and create a GitHub PR

### Usage

```bash
# Dry-run: just show generated patch
python dev/agents/agent.py --task "describe what to implement"

# Generate patch via LLM
python dev/agents/agent.py --task "describe task" --use-llm

# Full automation: generate, apply, push, open PR
python dev/agents/agent.py --task "describe task" --use-llm --apply --push --pr
```

### Required Environment Variables

| Variable | Purpose |
|---|---|
| `LLM_API_KEY` | OpenAI-compatible API key |
| `GITHUB_TOKEN` | GitHub token for PR creation |

### Agent Branch Naming

The agent automatically creates branches named `agent/YYYYMMDDHHMMSS`.

## CI/CD Workflows

### `agent.yml` (Manual Dispatch)
- Accepts a `task_description` input
- Calls GPT-4o-mini at `https://models.inference.ai.azure.com`
- Writes the result to `generated_code.py` and auto-commits

### `agent-ci.yml` (Push / PR / Dispatch)
1. **test job** — runs `pytest -q`, must pass before agent job
2. **agent job** — optional; runs if `run_agent` input is `true` or `AUTO_AGENT` env var is set; generates a patch, applies it, re-runs tests, and can open a PR

Secrets required in GitHub repository settings: `LLM_API_KEY`, `GITHUB_TOKEN`.

## Code Conventions

These conventions are derived from `.github/copilot-instructions.md`.

### Style
- Formatter: **Black** with 88-character line width
- Python version: **3.9+**
- Type annotations are strongly preferred on function signatures
- Avoid bare `except:` — always name the exception type

### Testing
- Tests go in `tests/` using **pytest**
- Write unit tests for all new functionality
- CI runs tests before any agent patch is applied

### Security
- Never hardcode secrets or API keys — use environment variables
- Review LLM-generated patches before merging

### Commit Messages
- Keep commits small and focused
- Write descriptive messages explaining *what* changed and *why*

## Key Files to Know

| File | Notes |
|---|---|
| `dev/agents/agent.py` | Full agent implementation; uses stdlib only (no third-party HTTP) |
| `pyproject.toml` | Dependencies: `fastapi>=0.128.0`, `requests>=2.32.5` |
| `generated_code.py` | LLM output; may have quality issues — review before trusting |
| `.github/copilot-instructions.md` | Source-of-truth coding guidelines (written in Japanese) |

## Git Branch Strategy

| Branch pattern | Purpose |
|---|---|
| `master` / `main` | Stable production code |
| `claude/...` | Claude-generated feature branches |
| `agent/YYYYMMDDHHMMSS` | Branches auto-created by the agent scaffold |

When working as an AI assistant on this repo, always develop on the designated `claude/` branch and push before the session ends.

## Important Notes for AI Assistants

- The `generated_code.py` file may contain deprecated or incorrect patterns from previous LLM runs — do not treat it as a reference implementation.
- `main.py` is a placeholder entry point; extend it when adding real functionality.
- The project has no database, Docker setup, or external services beyond the OpenAI-compatible API endpoint.
- When adding features, write corresponding tests in `tests/` and ensure `pytest -q` passes before committing.
