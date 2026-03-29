import json
import sys
from pathlib import Path

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent


CONFIG_PATH = Path(__file__).with_name("agentcore_strands_simple_config.json")


def load_config() -> dict:
    """設定ファイルを読み込み、必要なキーがそろっているか確認する。"""
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        print(f"[エラー] 設定ファイルが見つかりません: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"[エラー] 設定ファイルの JSON が不正です: {exc}", file=sys.stderr)
        sys.exit(1)

    required_keys = ["agent_model", "system_prompt", "default_user_message"]
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        print(
            f"[エラー] 設定ファイルに不足しているキーがあります: {', '.join(missing_keys)}",
            file=sys.stderr,
        )
        sys.exit(1)

    return config


CONFIG = load_config()
SYSTEM_PROMPT = CONFIG["system_prompt"]
DEFAULT_USER_MESSAGE = CONFIG["default_user_message"]
AGENT_MODEL = CONFIG["agent_model"]


app = BedrockAgentCoreApp()


print("[情報] strands.Agent を初期化しています...")
try:
    # 設定ファイルで指定したモデル ID で Agent を作成します。
    agent = Agent(model=AGENT_MODEL)
    print(f"[情報] Agentが {AGENT_MODEL} で初期化されました。")
except Exception as e:
    print("\n[エラー] Agentの初期化に失敗しました。", file=sys.stderr)
    print(f"詳細: {e}", file=sys.stderr)
    print("認証情報または Bedrock モデルへのアクセスを確認してください。", file=sys.stderr)
    sys.exit(1)


@app.entrypoint
def invocations(payload):
    """リクエストを受け取り、strands.Agent で応答を生成する。"""
    print("\n" + "=" * 50)

    # prompt が未指定のときは設定ファイルの既定メッセージを使います。
    user_message = payload.get("prompt", DEFAULT_USER_MESSAGE)
    print(f"[サーバー] strands.Agent にプロンプトを渡します: '{user_message}'")

    try:
        # システムプロンプトとユーザー入力を 1 つの入力としてモデルへ渡します。
        result = agent(f"{SYSTEM_PROMPT}\n\n{user_message}")
        response_data = {"result": result.message}
    except Exception as e:
        print(f"\n[エラー] strands.Agent の処理中にエラーが発生しました: {e}", file=sys.stderr)
        response_data = {"error": f"Agent processing error: {str(e)}"}

    print(f"[サーバー] 以下のレスポンスを返します: {response_data}")
    print("=" * 50 + "\n")
    return response_data


if __name__ == "__main__":
    print("[情報] BedrockAgentCoreAppを起動します...")
    print("[情報] http://localhost:8080 で待機します。")
    print("[情報] 停止するには Ctrl+C を押してください。")

    try:
        app.run()
    except KeyboardInterrupt:
        print("\n[情報] サーバーが停止されました。")
    except Exception as e:
        print(f"\n[エラー] サーバーの起動に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)
