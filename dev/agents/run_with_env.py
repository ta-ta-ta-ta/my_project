#!/usr/bin/env python3
import os
import sys
import runpy

# Configure LLM provider: use 'gh_copilot' to use GitHub Copilot CLI, or 'mock' for testing
USE_COPILOT = os.environ.get('USE_COPILOT', '1').lower() in ('1', 'true', 'yes')

here = os.path.dirname(__file__)

if USE_COPILOT:
    # Use GitHub Copilot CLI
    os.environ['LLM_PROVIDER'] = 'copilot'
    gh_path = r'C:\Program Files\GitHub CLI\gh.exe'
    if os.path.exists(gh_path):
        os.environ['GH_PATH'] = gh_path
    print(f"Using GitHub Copilot CLI (LLM_PROVIDER=copilot)")
else:
    # Use mock LLM script for testing
    mock = os.path.join(here, 'mock_llm.py')
    os.environ['LLM_PROVIDER'] = 'cli'
    os.environ['LLM_CLI_COMMAND'] = f'python {mock}'
    print(f"Using mock LLM (LLM_PROVIDER=cli)")

# Forward args to auto_develop
if len(sys.argv) == 1:
    print('Usage: run_with_env.py --task "..." [--dry-run]')
    sys.exit(1)
# Ensure sys.argv[0] is the script name
runpy.run_path(os.path.join(here, 'auto_develop.py'), run_name='__main__')
