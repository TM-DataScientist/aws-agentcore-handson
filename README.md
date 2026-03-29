# aws-agent-project

Amazon Bedrock AgentCore と Strands Agents を使ったローカルエージェント実装を試すためのサンプルプロジェクトです。

## 概要

このリポジトリは、ローカルで AgentCore アプリを起動し、`/invocations` エンドポイント経由で動作確認するための個人ハンズオン用コードをまとめたものです。

## 参照した書籍

このハンズオンは、以下の書籍を参照して進めています。

- 書籍名: AWSではじめるAIエージェント開発・運用
- 著者: 掌田 津耶乃
- 出版社: 日経BP
- Amazon: https://amzn.asia/d/0j3ySGG2

書籍の内容をベースにしつつ、このリポジトリには手元での検証や調整を含む差分が入る場合があります。

## 主なファイル

- `agentcore_strands1.py`: AgentCore のエントリポイント
- `client_requests.py`: ローカル `/invocations` エンドポイントを呼び出すクライアント
- `requirements.txt`: 実行に必要な Python パッケージ一覧
