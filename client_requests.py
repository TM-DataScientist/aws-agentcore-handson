import sys

import requests


# ローカルで起動している AgentCore サーバーの URL。
URL = "http://localhost:8080/invocations"

# JSON を送るだけなのでヘッダーは最小限でよい。
HEADERS = {"Content-Type": "application/json"}

# 入力が空だったときのデフォルトメッセージ。
DEFAULT_PROMPT = "Hello"


def extract_result_text(response_data: dict) -> str:
    """サーバー応答から、人が読みたい本文だけを取り出す。"""
    result = response_data.get("result")
    if isinstance(result, str):
        return result

    # 将来 result が構造化されても text を拾えるようにしておく。
    if isinstance(result, dict):
        content = result.get("content", [])
        if content and isinstance(content[0], dict) and isinstance(content[0].get("text"), str):
            return content[0]["text"]

    content = response_data.get("content", [])
    if content and isinstance(content[0], dict) and isinstance(content[0].get("text"), str):
        return content[0]["text"]

    error = response_data.get("error")
    if isinstance(error, str):
        return error

    return str(response_data)


def call_local_server():
    """ローカルサーバーに prompt を送り、回答を表示する。"""
    # 引数があれば引数を使い、なければ対話入力にする。
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    else:
        prompt = input("メッセージ: ").strip()

    payload = {"prompt": prompt or DEFAULT_PROMPT}

    print(f"[クライアント] サーバー ( {URL} ) にリクエストを送信します...")
    print(f"[クライアント] ペイロード: {payload}")

    try:
        response = requests.post(URL, headers=HEADERS, json=payload, timeout=60)
        response.raise_for_status()

        print("\n[クライアント] サーバーからのレスポンスを受信しました。")
        print(f"  ステータスコード: {response.status_code}")

        response_data = response.json()
        result_text = extract_result_text(response_data)
        print(f"\n  >> エージェントの回答: {result_text}")
    except requests.exceptions.ConnectionError:
        print("\n[エラー] サーバーへの接続に失敗しました。", file=sys.stderr)
        print(f"{URL} が起動しているか確認してください。", file=sys.stderr)
    except requests.exceptions.HTTPError as exc:
        print("\n[エラー] HTTPエラーが発生しました。", file=sys.stderr)
        print(f"詳細: {exc}", file=sys.stderr)
    except requests.exceptions.JSONDecodeError:
        print("\n[エラー] サーバー応答を JSON として解釈できません。", file=sys.stderr)
        print(f"応答本文: {response.text[:200]}...", file=sys.stderr)
    except Exception as exc:
        print(f"\n[エラー] 予期しないエラーが発生しました: {exc}", file=sys.stderr)


if __name__ == "__main__":
    call_local_server()
