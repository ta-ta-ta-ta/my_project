# Agent scaffold

このディレクトリは「エージェント風」の自動化の例を示します。

目的:
- ローカルでの自動開発ループを素早く試す。
- CI（GitHub Actions）から同じスクリプトを実行できるようにする。

使い方（ローカル）:
````markdown
# Agent scaffold

このディレクトリは「エージェント風」の自動化の例を示します。

目的:
- ローカルでの自動開発ループを素早く試す。
- CI（GitHub Actions）から同じスクリプトを実行できるようにする。

使い方（ローカル）:
```bash
# LLM を使わずテストだけ実行（dry-run）
python dev/agents/agent.py --task "Run tests and note next steps"

# LLM によるパッチ生成（dry-run: パッチを表示）
python dev/agents/agent.py --task "Add greet i18n support" --use-llm

# LLM パッチを適用してブランチ作成、コミット（--push と --pr は追加でリモート push と PR 作成）
python dev/agents/agent.py --task "Add greet i18n support" --use-llm --apply --push --pr
```

注意:
- LLM 機能を利用するには `LLM_API_KEY` を環境変数に設定してください（OpenAI 互換エンドポイントを使用）。
- `--apply` を指定すると `git apply --index` が実行されます。外部 API によるパッチは必ずレビューしてください。

拡張案:
- LLM でパッチを生成し `git apply` で当てる
- テストが通るまでループする監視ループ
- PR 作成を自動化するために GitHub API を呼ぶ

````
