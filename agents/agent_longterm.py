import json
import os
import re
import sys
from typing import Dict, List

from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent


REGION = "us-east-1"
MEMORY_ID = os.getenv("BEDROCK_AGENTCORE_MEMORY_ID", "")
AGENT_MODEL = "amazon.nova-lite-v1:0"
SESSION_ID = "PersonalSession1-abcdefg1234567890"
ACTOR_ID = "User100"
NAMESPACE = f"/users/{ACTOR_ID}"
PREFERENCE_MARKER = "PREFERENCE_JSON:"

if not MEMORY_ID:
    raise ValueError("BEDROCK_AGENTCORE_MEMORY_ID environment variable is required.")


app = BedrockAgentCoreApp()
memory_client = MemoryClient(region_name=REGION)


print("[情報] strands.Agent を初期化しています...")

SYSTEM_PROMPT = """
あなたはアクセスしたユーザーに特化したエージェントです。
過去のやり取りや記録済みの好みがあれば、それを優先して回答してください。
記録済みの情報が無い場合は、無いと正直に伝えてください。
不明な個人情報を推測で作らないでください。
"""


agent = Agent(
    model=AGENT_MODEL,
    system_prompt=SYSTEM_PROMPT,
)


def extract_preferences(text: str) -> List[Dict[str, str]]:
    """ユーザー発話から記録対象の好みを抽出する。"""
    preferences: List[Dict[str, str]] = []

    match = re.search(r"私の(?P<topic>.+?)は(?P<value>.+?)(?:です|だ)(?:[。.!！?？]|$)", text)
    if match:
        topic = match.group("topic").strip()
        value = match.group("value").strip()
        if topic and value:
            preferences.append({"topic": topic, "value": value})

    return preferences


def build_preference_message(preference: Dict[str, str]) -> str:
    """イベント保存用に、ASCII 安全な JSON 文字列へ変換する。"""
    return PREFERENCE_MARKER + json.dumps(preference, ensure_ascii=True, separators=(",", ":"))


def load_preferences_from_events() -> Dict[str, str]:
    """保存済みイベントから好み情報を復元する。"""
    preferences: Dict[str, str] = {}

    events = memory_client.list_events(
        memory_id=MEMORY_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
    )

    def sort_key(event: Dict) -> str:
        return str(event.get("eventTimestamp", ""))

    for event in sorted(events, key=sort_key):
        for payload_item in event.get("payload", []):
            conversational = payload_item.get("conversational", {})
            role = conversational.get("role")
            text = conversational.get("content", {}).get("text", "")
            if role != "TOOL" or not text.startswith(PREFERENCE_MARKER):
                continue

            try:
                preference = json.loads(text[len(PREFERENCE_MARKER) :])
            except json.JSONDecodeError:
                continue

            topic = str(preference.get("topic", "")).strip()
            value = str(preference.get("value", "")).strip()
            if topic and value:
                preferences[topic] = value

    return preferences


def retrieve_memory_records(query: str) -> List[Dict]:
    """Memory records があれば取得する。無ければ空配列を返す。"""
    try:
        response = memory_client.retrieve_memory_records(
            memory_id=MEMORY_ID,
            namespace=NAMESPACE,
            search_criteria={"searchQuery": query},
        )
    except Exception:
        return []

    return response.get("memoryRecordSummaries", [])


def detect_question_topic(text: str) -> str | None:
    """『私の好きな〇〇は何ですか？』のような質問から topic を取り出す。"""
    match = re.search(r"私の(?P<topic>.+?)は何(?:ですか|？|\?)", text)
    if match:
        return match.group("topic").strip()
    return None


def build_memory_context(preferences: Dict[str, str], memory_records: List[Dict]) -> str:
    """モデルに渡すための記憶コンテキストを組み立てる。"""
    sections: List[str] = []

    if preferences:
        preference_lines = [f"- {topic}: {value}" for topic, value in preferences.items()]
        sections.append("保存済みの好み:\n" + "\n".join(preference_lines))

    if memory_records:
        record_lines = []
        for record in memory_records[:5]:
            summary = record.get("summaryText") or record.get("memoryRecordId") or json.dumps(record, ensure_ascii=False)
            record_lines.append(f"- {summary}")
        sections.append("Memory records:\n" + "\n".join(record_lines))

    return "\n\n".join(sections)


def extract_agent_text(result) -> str:
    """strands.Agent の戻り値からテキストだけを取り出す。"""
    message = getattr(result, "message", "")
    if isinstance(message, str):
        return message
    if isinstance(message, dict):
        contents = message.get("content", [])
        if contents and isinstance(contents[0], dict):
            return str(contents[0].get("text", ""))
    return str(message)


def answer_from_preferences(user_message: str, preferences: Dict[str, str]) -> str | None:
    """好みに関する質問はコード側で確実に回答する。"""
    if not preferences:
        return None

    topic = detect_question_topic(user_message)
    if topic:
        value = preferences.get(topic)
        if value:
            return f"以前のやり取りでは、あなたの{topic}は{value}です。"
        return f"まだあなたの{topic}は記録されていません。"

    if "好みをまとめて" in user_message or "好みを教えて" in user_message:
        lines = [f"- {topic}: {value}" for topic, value in preferences.items()]
        return "今までに記録している好みは次のとおりです。\n" + "\n".join(lines)

    return None


def store_conversation(user_message: str, assistant_message: str, preferences: List[Dict[str, str]]) -> None:
    """会話内容と抽出した好みを Memory サービスへ保存する。"""
    messages = [(user_message, "USER")]

    # 検索用の好みは TOOL メッセージとして ASCII JSON で保存する。
    for preference in preferences:
        messages.append((build_preference_message(preference), "TOOL"))

    messages.append((assistant_message, "ASSISTANT"))

    memory_client.create_event(
        memory_id=MEMORY_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        messages=messages,
    )


@app.entrypoint
def invocations(payload):
    """リクエストを受け取り、長期記憶を参照しながら回答する。"""
    print("\n" + "=" * 50)

    user_message = str(payload.get("prompt", "Hello! How can I help you today?")).strip()
    if not user_message:
        return {"error": "prompt is required"}

    print(f"[サーバー] 受信メッセージ: '{user_message}'")

    try:
        preferences = load_preferences_from_events()
        memory_records = retrieve_memory_records(user_message)

        # 好みに関する定型質問はコード側で優先的に処理する。
        direct_answer = answer_from_preferences(user_message, preferences)
        if direct_answer:
            assistant_message = direct_answer
        else:
            memory_context = build_memory_context(preferences, memory_records)
            prompt = user_message
            if memory_context:
                prompt = (
                    "以下はこのユーザーについて覚えている情報です。\n"
                    f"{memory_context}\n\n"
                    f"ユーザーの質問: {user_message}"
                )
            result = agent(prompt)
            assistant_message = extract_agent_text(result)

        new_preferences = extract_preferences(user_message)
        store_conversation(user_message, assistant_message, new_preferences)

        response_data = {"result": assistant_message}
    except Exception as e:
        print(f"\n[エラー] 長期記憶エージェントの処理中にエラーが発生しました: {e}", file=sys.stderr)
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
