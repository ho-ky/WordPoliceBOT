# 本番デプロイ手順（MWS）

## 事前確認

- Supabaseのマイグレーションを適用し、`npx supabase migration list`でlocal/remoteの番号が一致することを確認する。
- `npx supabase db advisors --linked --type all --level warn`で警告を確認する。
- 本番DiscordサーバーでDeveloper Modeを有効にし、サーバーIDを控える。
- Discord Developer PortalでMessage Content Intentを有効にする。
- Botを新しいサーバーへ招待し、メッセージ閲覧・送信とSlash Command利用に必要な権限を付与する。

## MWSに配置するもの

Python Botとして、このリポジトリのソースと`requirements.txt`を配置する。起動ファイルは`bot.py`、起動コマンドの指定欄がある場合は`python bot.py`を使う。`.env`、`.venv/`、`node_modules/`、`supabase/.temp/`はアップロードしない。依存ライブラリが自動導入されるか、MWSの管理画面で確認する。

MWSの環境変数に次を設定する。値はチャットやGitへ貼らない。

- `DISCORD_TOKEN`：再生成済みのBotトークン。
- `DATABASE_URL`：Supabase Dashboardの「Connect」からコピーしたSession poolerのPostgreSQL接続文字列。通常はポート5432。パスワードを入れ、必要に応じて`sslmode=require`を指定する。
- `COMMAND_GUILD_ID`：新しいDiscordサーバーのID。未設定ではグローバルコマンド同期になる。

既に同じBotをグローバルコマンドで動かしていた場合、サーバーIDを設定するだけではDiscord上の古いグローバルコマンドは削除されない。新サーバーでの動作確認後、旧サーバーからBotを外し、必要に応じてグローバルコマンドを整理する。

MWSから直接接続できるかはデプロイ後のログで確認する。Bot起動時は`watch_words`と`detections`の存在を確認するため、接続失敗時はSlash Command同期前にエラーになる。

## 起動後の確認

1. 同じトークンを使うローカルBotを停止してからMWS側を起動する。
2. MWSのログでPostgreSQL接続エラーとDiscordログインエラーがないことを確認する。
3. 新しいサーバーで`/ping`、`/word add`、`/word list`を試す。
4. 通常メッセージでワード検出・返信・`/word stats`を試す。
5. 同数のデータを作り、`/word trend`と`/word ranking`が同順位になることを確認する。
6. Supabaseのテーブルに新サーバーのデータだけが増えることを確認する。

旧SQLiteの試験データは移行しない。MWSの無料プランにはリソース上限と、現在7日間更新がないBotの休眠条件があるため、継続運用時は[利用規約](https://cloud.m-ws.cc/terms)を確認する。
