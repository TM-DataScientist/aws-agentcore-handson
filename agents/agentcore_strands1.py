import random
import re
import sys

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool


# 利用するモデル ID。
# このサンプルでは、天気以外の雑談にだけ LLM を使う。
MODEL_ID = "amazon.nova-lite-v1:0"

# 都市名が取れなかった場合のフォールバック先。
DEFAULT_CITY = "東京"

# 「天気の質問かどうか」をざっくり判定するためのキーワード群。
WEATHER_KEYWORDS = ("天気", "気温", "weather", "forecast")

# モデルが thinking タグを返した場合に落とすための正規表現。
THINKING_PATTERN = re.compile(r"<thinking>.*?</thinking>\s*", re.DOTALL)

# 質問文から都市名を抜くための簡単なパターン。
CITY_PATTERNS = (
    re.compile(r"(?P<city>.+?)の天気"),
    re.compile(r"(?P<city>.+?)の気温"),
    re.compile(r"weather in (?P<city>.+)", re.IGNORECASE),
    re.compile(r"forecast for (?P<city>.+)", re.IGNORECASE),
)


def is_weather_question(text: str) -> bool:
    """入力が天気に関する質問かどうかを判定する。"""
    lowered = text.lower()
    return any(keyword in text or keyword in lowered for keyword in WEATHER_KEYWORDS)


def extract_city(text: str) -> str:
    """質問文から都市名らしき部分を抜き出す。"""
    prompt = text.strip()

    for pattern in CITY_PATTERNS:
        match = pattern.search(prompt)
        if match:
            city = match.group("city").strip(" 　?？.,。")
            if city:
                return city

    # 定型句を取り除いた残りを都市名候補として扱う。
    cleaned = re.sub(
        r"(天気|気温|weather|forecast|を教えてください|を教えて|教えて|知りたい)",
        " ",
        prompt,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" 　?？.,。")
    return cleaned or DEFAULT_CITY


def build_weather_data(city: str) -> dict:
    """都市名をもとに、再現性のあるサンプル天気データを作る。"""
    normalized_city = city.strip() or DEFAULT_CITY

    # 都市名を seed に使うことで、同じ都市なら毎回同じ結果になる。
    rng = random.Random(normalized_city)
    weather_options = [
        "晴れ",
        "くもり",
        "雨",
        "晴れのちくもり",
        "くもりのち雨",
        "雨のち晴れ",
    ]
    min_temp = rng.randint(6, 18)
    max_temp = rng.randint(min_temp + 3, min_temp + 11)
    return {
        "city": normalized_city,
        "weather": rng.choice(weather_options),
        "max_temp": max_temp,
        "min_temp": min_temp,
    }


@tool
def my_tool(city: str = DEFAULT_CITY) -> dict:
    """指定した都市のサンプル天気情報を返す。"""
    weather = build_weather_data(city)
    print(f"[tool] my_tool called for city={weather['city']}")
    return weather


def format_weather_reply(weather: dict) -> str:
    """ツール結果を日本語の回答文に整形する。"""
    return (
        f"{weather['city']}の天気は{weather['weather']}です。"
        f"最高気温は{weather['max_temp']}度、最低気温は{weather['min_temp']}度です。"
    )


def sanitize_agent_text(text: str) -> str:
    """モデルの生テキストから thinking や接頭辞を取り除く。"""
    cleaned = THINKING_PATTERN.sub("", text).strip()
    cleaned = cleaned.replace("[アシスタント]:", "").strip()
    return cleaned


# AgentCore のローカルアプリ本体。
app = BedrockAgentCoreApp()


# 天気以外の入力に対する、通常会話用のシステムプロンプト。
SYSTEM_PROMPT = """
あなたは天気案内アシスタントです。
- 日本語で簡潔に回答してください。
- thinking や推論過程、XML タグは出力しないでください。
- 天気の質問では my_tool を使ってよいですが、最終回答は自然な日本語だけにしてください。
- 天気以外の質問には簡潔に答えてください。
""".strip()


print("[情報] strands.Agent を初期化しています...")
try:
    # callback_handler=None にして、不要な標準出力を減らしている。
    agent = Agent(
        model=MODEL_ID,
        tools=[my_tool],
        system_prompt=SYSTEM_PROMPT,
        callback_handler=None,
    )
    print(f"[情報] Agent がモデル {MODEL_ID} で初期化されました。")
except Exception as exc:
    print(f"[エラー] strands.Agent の初期化に失敗しました: {exc}", file=sys.stderr)
    sys.exit(1)


@app.entrypoint
def invoke(payload):
    """POST /invocations を受け取り、回答 JSON を返す。"""
    print("=" * 50)
    print(f"[server] payload={payload}")

    user_message = str(payload.get("prompt", "")).strip()
    if not user_message:
        return {"error": "prompt is required"}

    try:
        # 天気質問なら都市名を抜いてローカルツール結果を返す。
        if is_weather_question(user_message):
            city = extract_city(user_message)
            weather = my_tool(city)
            response_text = format_weather_reply(weather)
            response_data = {"result": response_text}
        else:
            # それ以外は通常の LLM 応答を返す。
            result = agent(user_message)
            response_text = sanitize_agent_text(str(result))
            response_data = {
                "result": response_text or "質問内容をもう少し詳しく教えてください。"
            }
    except Exception as exc:
        print(f"[エラー] Agent の処理に失敗しました: {exc}", file=sys.stderr)
        response_data = {"error": f"Agent processing error: {exc}"}

    print(f"[server] response={response_data}")
    print("=" * 50)
    return response_data


if __name__ == "__main__":
    print("[情報] BedrockAgentCoreApp ローカルサーバーを起動します...")
    print("[情報] http://localhost:8080 で待機中")
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n[情報] サーバーを停止しました。")
    except Exception as exc:
        print(f"[エラー] サーバー起動に失敗しました: {exc}", file=sys.stderr)
        sys.exit(1)
