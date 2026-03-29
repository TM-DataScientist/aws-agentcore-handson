import json
import os
import sys
import uuid

import boto3


REGION = "us-east-1"
MEMORY_ID = os.getenv("BEDROCK_AGENTCORE_MEMORY_ID", "")
AGENT_RUNTIME_ARN = os.getenv("BEDROCK_AGENT_RUNTIME_ARN", "")

if not MEMORY_ID:
    raise ValueError("BEDROCK_AGENTCORE_MEMORY_ID environment variable is required.")

if not AGENT_RUNTIME_ARN:
    raise ValueError("BEDROCK_AGENT_RUNTIME_ARN environment variable is required.")


def add_accept_header(request, **kwargs):
    request.headers.add_header("Accept", "text/event-stream, application/json")


if len(sys.argv) > 1:
    prompt = sys.argv[1]
else:
    prompt = input("prompt: ")

client = boto3.client("bedrock-agentcore", region_name=REGION)
payload = json.dumps({"prompt": prompt})

# デプロイ済みの長期記憶エージェントを呼び出します。
# MEMORY_ID はエージェント側の設定確認用として残しています。
handler_id = client.meta.events.register_first(
    "before-sign.bedrock-agentcore.InvokeAgentRuntime",
    add_accept_header,
)

try:
    response = client.invoke_agent_runtime(
        agentRuntimeArn=AGENT_RUNTIME_ARN,
        runtimeSessionId=str(uuid.uuid4()),
        payload=payload,
        contentType="application/json",
        qualifier="DEFAULT",
    )
    response_body = response["response"].read()
    response_data = json.loads(response_body)
    print("Memory ID:", MEMORY_ID)
    print("Agent Response:", response_data)
finally:
    client.meta.events.unregister(
        "before-sign.bedrock-agentcore.InvokeAgentRuntime",
        handler_id,
    )
