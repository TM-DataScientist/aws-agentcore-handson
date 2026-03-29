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

## ディレクトリ構成

- `agents/`: AgentCore のエントリポイントやエージェント実装
- `scripts/`: 呼び出し用クライアントや補助スクリプト
- `mcp/`: MCP サーバーとクライアント例
- `memory/`: Memory API の検証用スクリプト
- `config/`: エージェント設定ファイル
- `policies/`: ポリシー JSON

## 主なファイル

- `agents/agentcore_strands1.py`: AgentCore のメインエントリポイント
- `agents/agent_longterm.py`: Memory を使う長期記憶エージェント。`BEDROCK_AGENTCORE_MEMORY_ID` が必要
- `scripts/client_requests.py`: ローカル `/invocations` エンドポイントを呼び出すクライアント
- `mcp/mcp_client3.py`: 対話式の MCP クライアント例
- `requirements.txt`: 実行に必要な Python パッケージ一覧
