# Bot 基盤仕様

## 目的

Bot を起動し、Discord への接続、設定読み込み、SQLite 初期化、Slash Command の同期を行うための土台を定義します。

## 起動方式

Bot Token は `.env` から読み込みます。

挙動の詳細:

- 起動時に `.env` から設定を読み込みます。
- 読み込んだ設定をもとに SQLite 初期化と Slash Command の同期を行います。
- メッセージ本文を扱うため、Message Content Intent を有効にします。

## 必要な環境変数

- `DISCORD_TOKEN`
- `DATABASE_PATH`  `任意`  `既定: data/wordpolice.db`
- `COMMAND_GUILD_ID`  `任意`

実装上のメモ:

- `DATABASE_PATH` が未指定の場合は既定パスを使用します。
- `COMMAND_GUILD_ID` が未指定の場合はグローバルに Slash Command を同期します。
- 環境変数の読み込み失敗は起動前に検出できるようにします。

## Discord Intents

メッセージ本文を検出するため、Message Content Intent を使用します。

補足:

- 必要最小限の Intents を有効にします。
- メッセージ検出が不要な用途では追加の Intent は使いません。

## コマンド方式

Slash Command を使用します。

挙動の詳細:

- コマンドは起動時に同期します。
- 開発時は特定サーバーへの同期を優先できるようにします。

## 初期化処理

Bot 起動時に以下を行います。

1. 環境変数の読み込み
2. SQLite 接続
3. 必要テーブルの作成
4. Slash Command の同期

実装上のメモ:

- DB 初期化は Bot 起動時に一度だけ行います。
- テーブル作成は冪等に実行できるようにします。
- 失敗時は起動を中断し、原因をログに残します。

## 実装方針

- 設定値は `config.py` でまとめて扱う
- DB 初期化は `database.py` に分離する
- Bot 本体は `bot.py` から起動する
- まずは起動確認用の最小コマンドを用意して、セットアップの検証をしやすくする

## DB 初期化対象

最初の段階では、将来の機能追加を見越して次のテーブルを用意します。

- `guild_settings`
- `watch_words`
- `detections`

補足:

- `guild_settings` は通知先チャンネルなどのサーバー単位設定を保持します。
- `watch_words` は監視ワード本体を保持します。
- `detections` は検出履歴を保持します。
