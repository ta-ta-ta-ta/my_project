# My Project

This repository contains a small agent scaffold to help automate development tasks
for an asset-management feature using multiple simulated project members (personas).

## Agents / Personas

Personas are defined in `dev/agents/personas.json` and include:

- `user`: End User / Product Owner
- `pm`: Product Manager
- `expert`: Asset Management Expert
- `engineer`: Engineer
- `web_designer`: Web Designer
- `system_architect`: System Architect
- `app_specialist`: Application Specialist
- `db_specialist`: DB Specialist
- `network_specialist`: Network Specialist
- `security_specialist`: Security Specialist
- `strategist`: Strategist

## Orchestrator: `dev/agents/auto_develop.py`

The orchestrator loads each persona from `personas.json`, constructs a prompt
for each, and asks the LLM (via `dev/agents/agent.py`) to produce a unified diff
patch. It can optionally apply the patch, run tests, push a branch, and open a PR.

Usage examples:

```bash
# Dry-run (show patches only, no apply)
python dev/agents/auto_develop.py --task "Add portfolio allocation feature" --use-llm --dry-run

# Apply patches, run tests, push and create PR (requires LLM_API_KEY, GITHUB_TOKEN)
python dev/agents/auto_develop.py --task "Add portfolio allocation feature" --use-llm --apply --push --pr
```

Files of interest:

- `dev/agents/agent.py` — LLM call helpers, git helpers, test runner
- `dev/agents/personas.json` — persona definitions
- `dev/agents/auto_develop.py` — multi-persona orchestrator

## Environment variables

- `LLM_API_KEY`: API key for LLM provider (required for `--use-llm`).
- `GITHUB_TOKEN`: token to create PRs from the agent (repo scope required).
- `SKIP_TESTS`: set to `1` to skip running tests (or use `--skip-tests`).

CI: A sample GitHub Actions workflow is added at `.github/workflows/agent-ci.yml`.
