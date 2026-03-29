import os
import re

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from langchain.agents import create_agent
from langchain_aws import ChatBedrockConverse
from langchain_core.tools import tool


AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")


# Bedrock の Converse API を使うモデルを初期化する。
llm = ChatBedrockConverse(
    model=BEDROCK_MODEL_ID,
    region_name=AWS_REGION,
    temperature=0,
)


@tool
def get_weather(city: str) -> str:
    """指定された都市の天気を返すサンプルツール。"""
    # 実運用ではここで外部 API を叩く
    return f"It's always sunny in {city}!"


tools = [get_weather]
agent = create_agent(llm, tools)
app = BedrockAgentCoreApp()


def normalize_content(content):
    """LangChain の返却内容から見やすい最終テキストを取り出す。"""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                text_parts.append(str(item["text"]))
            else:
                text_parts.append(str(item))
        text = "\n".join(text_parts)
    else:
        text = str(content)

    response_match = re.search(r"<response>(.*?)</response>", text, re.DOTALL)
    if response_match:
        return response_match.group(1).strip()

    thinking_removed = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL)
    return thinking_removed.strip()


@app.entrypoint
def invoke(payload):
    location = payload.get("prompt", "tokyo")


    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": f"what is the weather in {location}"}]}
        )
    except Exception as e:
        return {"error": f"Agent invocation failed: {e}"}


    # result の構造を安全に扱う
    messages = result.get("messages") if isinstance(result, dict) else None
    if not messages:
        return {"error": "Agent returned no messages."}


    last_msg = messages[-1]
    content = getattr(last_msg, "content", None) or last_msg.get("content")
    return {"result": normalize_content(content)}


if __name__ == "__main__":
    app.run()
