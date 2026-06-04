# WordPoliceBOT

Discord サーバー内のメッセージから、ユーザーが設定した任意の言葉を検出して記録する Bot です。

## 技術構成

- Python
- discord.py
- SQLite

## 現在の状態

- Bot 起動の土台を実装済み
- SQLite の初期化を実装済み
- Slash Command の同期基盤を実装済み

## セットアップ

1. `python -m venv .venv`
2. 仮想環境を有効化する
3. `pip install -r requirements.txt`
4. `.env.example` を元に `.env` を作成する
5. `python bot.py` で起動する

## 環境変数

- `DISCORD_TOKEN`
- `DATABASE_PATH`
- `COMMAND_GUILD_ID`

## 備考

ワード管理、検出、集計の各コマンドは次の段階で追加します。
