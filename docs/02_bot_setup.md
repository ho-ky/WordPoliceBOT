# Bot 基盤仕様

## 目的

Bot を起動し、Discord への接続、設定読み込み、SQLite 初期化、Slash Command の同期を行うための土台を定義します。

## 起動方式

Bot Token は `.env` から読み込みます。

## 必要な環境変数

- `DISCORD_TOKEN`
- `DATABASE_PATH`  `任意`  `既定: data/wordpolice.db`
- `COMMAND_GUILD_ID`  `任意`

## Discord Intents

メッセージ本文を検出するため、Message Content Intent を使用します。

## コマンド方式

Slash Command を使用します。

## 初期化処理

Bot 起動時に以下を行います。

1. 環境変数の読み込み
2. SQLite 接続
3. 必要テーブルの作成
4. Slash Command の同期

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
