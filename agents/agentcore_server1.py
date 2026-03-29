from bedrock_agentcore.runtime import BedrockAgentCoreApp


# ローカルで動かす AgentCore アプリを作成する。
# このアプリは POST /invocations や GET /ping などのエンドポイントを公開する。
app = BedrockAgentCoreApp()


# メインのリクエスト処理を登録する。
# /invocations に送られた JSON ボディが `payload` として渡される。
@app.entrypoint
def invoke(payload):
    """受け取った prompt をそのまま返すシンプルなサンプル。"""
    # リクエストボディからユーザーの prompt を取り出す。
    # prompt が無い場合は "Hello" を使う。
    user_message = payload.get("prompt", "Hello")

    # この dict は AgentCore により JSON のレスポンスとして返される。
    return {"result": user_message}


if __name__ == "__main__":
    # デフォルトでは http://127.0.0.1:8080 でローカルサーバーを起動する。
    app.run()
