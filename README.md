# WordPoliceBOT

Discord サーバー内のメッセージから、ユーザーが設定した任意の言葉を検出して記録する Bot です。

## 技術構成

- Python
- discord.py
- SQLite
- python-dotenv

## 現在の状態

- Bot 起動の土台を実装済み
- SQLite の初期化を実装済み
- Slash Command の同期基盤を実装済み
- 監視ワードの追加・一覧・編集・削除を実装済み
- メッセージ検出と検出ログ保存を実装済み
- 検出数集計とランキング表示を実装済み

## コマンド一覧

- `/ping`
- `/word add`
- `/word list`
- `/word edit`
- `/word delete`
- `/word stats`
- `/word ranking`

## セットアップ

1. `python -m venv .venv`
2. 仮想環境を有効化する
3. `pip install -r requirements.txt`
4. `.env.example` を元に `.env` を作成する
5. `python bot.py` で起動する

## 環境変数

- `DISCORD_TOKEN`
- `DATABASE_PATH`  `任意`  `既定: data/wordpolice.db`
- `COMMAND_GUILD_ID`

## 備考

- 検出ログの `detected_at` は UTC で保存します。
- 期間指定の入力は日本時間（JST）で解釈する前提です。
- `.env` と実運用 DB はリポジトリに含めません。
