import random
import re
import sys

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool


MODEL_ID = "amazon.nova-lite-v1:0"
DEFAULT_CITY = "東京"
WEATHER_KEYWORDS = ("天気", "気温", "weather", "forecast")
THINKING_PATTERN = re.compile(r"<thinking>.*?</thinking>\s*", re.DOTALL)
CITY_PATTERNS = (
    re.compile(r"(?P<city>.+?)の天気"),
    re.compile(r"(?P<city>.+?)の気温"),
    re.compile(r"weather in (?P<city>.+)", re.IGNORECASE),
    re.compile(r"forecast for (?P<city>.+)", re.IGNORECASE),
)


def is_weather_question(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in text or keyword in lowered for keyword in WEATHER_KEYWORDS)


def extract_city(text: str) -> str:
    prompt = text.strip()

    for pattern in CITY_PATTERNS:
        match = pattern.search(prompt)
        if match:
            city = match.group("city").strip(" 　?？.,。")
            if city:
                return city

    cleaned = re.sub(r"(天気|気温|weather|forecast|を教えてください|を教えて|教えて|知りたい)", " ", prompt, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" 　?？.,。")
    return cleaned or DEFAULT_CITY


def build_weather_data(city: str) -> dict:
    normalized_city = city.strip() or DEFAULT_CITY
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
    return (
        f"{weather['city']}の天気は{weather['weather']}です。"
        f"最高気温は{weather['max_temp']}度、最低気温は{weather['min_temp']}度です。"
    )


def sanitize_agent_text(text: str) -> str:
    cleaned = THINKING_PATTERN.sub("", text).strip()
    cleaned = cleaned.replace("[アシスタント]:", "").strip()
    return cleaned


app = BedrockAgentCoreApp()


SYSTEM_PROMPT = """
あなたは天気案内アシスタントです。
- 日本語で簡潔に回答してください。
- thinking や推論過程、XML タグは出力しないでください。
- 天気の質問では my_tool を使ってよいですが、最終回答は自然な日本語だけにしてください。
- 天気以外の質問には簡潔に答えてください。
""".strip()


print("[情報] strands.Agent を初期化しています...")
try:
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
    """Handle POST /invocations requests."""
    print("=" * 50)
    print(f"[server] payload={payload}")

    user_message = str(payload.get("prompt", "")).strip()
    if not user_message:
        return {"error": "prompt is required"}

    try:
        if is_weather_question(user_message):
            city = extract_city(user_message)
            weather = build_weather_data(city)
            response_text = format_weather_reply(weather)
            response_data = {"result": response_text}
        else:
            result = agent(user_message)
            response_text = sanitize_agent_text(str(result))
            response_data = {"result": response_text or "質問内容をもう少し詳しく教えてください。"}
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
