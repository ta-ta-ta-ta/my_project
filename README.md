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

LLM provider options
- `LLM_PROVIDER`: set to one of the following:
  - `openai` (default): uses OpenAI API (requires `LLM_API_KEY`)
  - `vscode` / `vscode_chat`: uses VS Code Copilot Chat API (requires GitHub Copilot subscription and `VSCODE_COPILOT_HELPER` script)
  - `copilot` / `gh_copilot`: uses GitHub CLI Copilot extension (requires `gh` CLI with copilot extension)
  - `cli`: uses a custom CLI tool (requires `LLM_CLI_COMMAND`)

### Using VS Code Copilot Chat (recommended if you have Copilot subscription)

**Requirements:**
- GitHub Copilot subscription (Individual $10/mo, Business $19/user/mo, or Enterprise $39/user/mo)
- VS Code with GitHub Copilot extension installed and signed in
- Helper script to bridge Python and VS Code Chat API

**Setup:**
1. Create a helper script (e.g., `vscode_copilot_helper.js` or `.py`) that:
   - Reads the prompt from the first argument (file path)
   - Calls VS Code Copilot Chat API (via VS Code extension API or task)
   - Writes the response to the second argument (output file path)

2. Set environment variables:
```powershell
$env:LLM_PROVIDER = "vscode"
$env:VSCODE_COPILOT_HELPER = "node path/to/vscode_copilot_helper.js"
```

**Note:** A sample helper script will be added in future updates. For now, you can use `openai` provider with API key or `cli` provider with a local LLM.

### Using CLI provider (for local LLMs like Ollama)

```powershell
$env:LLM_PROVIDER = "cli"
$env:LLM_CLI_COMMAND = "ollama run codellama"
```

CI: A sample GitHub Actions workflow is added at `.github/workflows/agent-ci.yml`.
