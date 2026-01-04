# VS Code Extension for Copilot Chat Integration

This directory contains a placeholder for a VS Code extension that integrates with GitHub Copilot Chat.

## Why an extension is needed

VS Code's Copilot Chat API (`vscode.lm.sendChatRequest`) is only accessible from within VS Code extensions. It cannot be called directly from external Node.js scripts or Python code.

## How to create the extension

1. Create a new VS Code extension project:
```bash
npm install -g yo generator-code
yo code
# Choose "New Extension (TypeScript)"
```

2. Add a command in `package.json`:
```json
{
  "contributes": {
    "commands": [
      {
        "command": "copilot-agent.sendPrompt",
        "title": "Send Prompt to Copilot Chat"
      }
    ]
  }
}
```

3. Implement the command in `src/extension.ts`:
```typescript
import * as vscode from 'vscode';
import * as fs from 'fs';

export function activate(context: vscode.ExtensionContext) {
    let disposable = vscode.commands.registerCommand('copilot-agent.sendPrompt', async (promptFile: string, outputFile: string) => {
        try {
            const prompt = fs.readFileSync(promptFile, 'utf-8');
            
            // Call Copilot Chat API
            const messages = [vscode.LanguageModelChatMessage.User(prompt)];
            const chatRequest = await vscode.lm.sendChatRequest(
                'copilot',
                messages,
                {},
                new vscode.CancellationTokenSource().token
            );
            
            let response = '';
            for await (const chunk of chatRequest.text) {
                response += chunk;
            }
            
            fs.writeFileSync(outputFile, response);
        } catch (error: any) {
            fs.writeFileSync(outputFile, `ERROR: ${error.message}`);
        }
    });

    context.subscriptions.push(disposable);
}
```

4. Install and test the extension:
```bash
npm install
npm run compile
# Press F5 to launch Extension Development Host
```

5. Set the environment variable to use the extension:
```powershell
$env:LLM_PROVIDER = "vscode"
$env:VSCODE_COPILOT_HELPER = "code --command copilot-agent.sendPrompt"
```

## Alternative: Use mock or other providers

Until the extension is ready, you can use:
- Mock LLM: Set `USE_COPILOT=0` in `run_with_env.py`
- OpenAI API: Set `LLM_PROVIDER=openai` and `LLM_API_KEY`
- Local LLM (Ollama): Set `LLM_PROVIDER=cli` and `LLM_CLI_COMMAND="ollama run codellama"`
