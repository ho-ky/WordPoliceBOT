# Bot 基盤仕様

## 目的

Bot を起動し、Discord への接続、設定の読み込み、SQLite の初期化、および Slash Command の同期を行います。

## 起動方式

Bot Token は `.env` から読み込みます。

## 必要な環境変数

- `DISCORD_TOKEN`
- `DATABASE_PATH`（任意、既定: `data/wordpolice.db`）
- `COMMAND_GUILD_ID`（任意）

## Discord Intents

メッセージ本文の検出には Message Content Intent を有効にします。

## コマンド方式

Bot は Slash Command を使用し、起動時にコマンドをサーバーに同期します。

## 初期化処理

Bot 起動時に以下を行います。

1. 環境変数の読み込み
2. SQLite 接続
3. 必要テーブルの作成
4. Slash Command の同期

## 期待される動作

- 設定値が未定義の場合、起動時に明確なエラーを検出できる。
- 監視対象のメッセージ本文を扱うため、必要な Intent を有効にする。
- 開発環境では特定サーバーへコマンドを同期できる。
- 本番環境ではグローバル同期を行うか、必要に応じて限定同期を選択できる。
