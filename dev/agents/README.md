# Agent scaffold

このディレクトリは「エージェント風」の自動化の例を示します。

目的:
- ローカルでの自動開発ループを素早く試す。
- CI（GitHub Actions）から同じスクリプトを実行できるようにする。

使い方（ローカル）:
```bash
python dev/agents/agent.py --task "Implement greet() with i18n"    # dry-run
python dev/agents/agent.py --task "Add feature X" --apply      # create branch + commit
```

注意:
- このスクリプトは安全のため最小限の動作のみ行います。自動で外部 API を呼ぶ機能は実装されていません。
- LLM を使った自律的な編集を行う場合、`LLM_API_KEY` 等のシークレットを環境変数／GitHub Secrets に設定してください。

拡張案:
- LLM でパッチを生成し `git apply` で当てる
- テストが通るまでループする監視ループ
- PR 作成を自動化するために GitHub API を呼ぶ
