# WordPoliceBOT

Discord サーバー内のメッセージから、ユーザーが設定した任意の言葉を検出して記録する Bot です。

## 技術構成

- Python
- discord.py
- Supabase PostgreSQL
- python-dotenv

## 現在の状態

- Bot 起動の土台を実装済み
- SupabaseマイグレーションとPostgreSQL接続を実装済み
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
- `/word trend`

## ローカルセットアップ

1. `uv venv`
2. `uv pip install --python .venv/bin/python -r requirements.txt -r requirements-dev.txt`
3. `npm ci`
4. `npx supabase start`、`npx supabase db reset`
5. `.env.example`を元に`.env`を作成し、Discord Botトークンを設定
6. `.venv/bin/python -m pytest -q`でテスト
7. `.venv/bin/python bot.py`で起動

本番DBのテーブルはBot起動時には作成しません。マイグレーションは`npx supabase db push`で適用します。

## 環境変数

- `DISCORD_TOKEN`
- `DATABASE_URL`（必須。ローカルまたはSupabaseのPostgreSQL接続文字列）
- `COMMAND_GUILD_ID`（任意。空欄ならグローバル、新サーバーに限定するならそのサーバーID）

## 注意事項

- 検出ログの `detected_at` は UTC で保存します。
- 期間指定の入力は日本時間（JST）で解釈する前提です。
- `.env`やDB接続パスワードはリポジトリに含めません。
