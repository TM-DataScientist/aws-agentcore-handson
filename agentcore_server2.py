import sys
import json
from bedrock_agentcore.runtime import BedrockAgentCoreApp


# アプリケーションのインスタンス作成
app = BedrockAgentCoreApp()


# エントリーポイント
@app.entrypoint
def invoke(payload):
    """
    BedrockAgentCoreApp がリクエストを受け取ったときに
    呼び出されるメインの関数。
    
    引数 (payload):
        リクエストの本体 (JSON)。
        boto3から呼ばれる場合、InvokeAgentのパラメータが入る。
        HTTP (curl) から呼ばれる場合、POSTされたJSONデータが入る。


    戻り値 (dict):
        エージェントの実行結果。
        この辞書がJSONに変換されてレスポンスとして返される。
    """
    
    print("\n" + "="*50)
    print("[サーバー] /invoke エンドポイントが呼び出されました。")
    print(f"[サーバー] 受け取ったペイロード: {payload}")


    # ペイロードから "prompt" キーの値を取得
    # もし "prompt" キーが存在しなければ、"Hello" をデフォルト値として使用
    user_message = payload.get("prompt", "Hello")
    
    # "オウム返し" のレスポンスを作成
    response_data = {
        "result": f"オウム返し: {user_message}"
    }
    
    print(f"[サーバー] 以下のレスポンスを返します: {response_data}")
    print("="*50 + "\n")


    # レスポンス（辞書）を返す
    return response_data


# サーバーの実行
if __name__ == "__main__":
    """
    このファイル (agent_server2.py) が直接実行された場合にのみ、
    以下の処理（サーバー起動）を行う。
    """
    print("[情報] BedrockAgentCoreApp ローカルサーバーを起動します...")
    print("[情報] デフォルトでは http://localhost:8080 で待機します。")
    print("[情報] 停止するには Ctrl+C を押してください。")
    
    try:
        # app.run() が、Webサーバーを起動し、
        # 外部からのリクエスト待機状態に入る
        app.run()
        
    except KeyboardInterrupt:
        print("\n[情報] サーバーが停止されました。")
    except Exception as e:
        print(f"\n[エラー] サーバーの起動に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)