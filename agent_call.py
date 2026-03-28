import json
import sys
import uuid

import boto3


client = boto3.client("bedrock-agentcore", region_name="us-east-1")


if len(sys.argv) > 1:
    prompt = sys.argv[1]
else:
    prompt = input("prompt: ")
payload = json.dumps({"prompt": prompt})


def add_accept_header(request, **kwargs):
    request.headers.add_header("Accept", "text/event-stream, application/json")


handler_id = client.meta.events.register_first(
    "before-sign.bedrock-agentcore.InvokeAgentRuntime",
    add_accept_header,
)


try:
    response = client.invoke_agent_runtime(
        agentRuntimeArn="arn:aws:bedrock-agentcore:us-east-1:927852416082:runtime/agentcore_strands1-pr0Zo18Ulz",
        runtimeSessionId=str(uuid.uuid4()),
        payload=payload,
        contentType="application/json",
        qualifier="DEFAULT",
    )
    response_body = response["response"].read()
    response_data = json.loads(response_body)
    print("Agent Response:", response_data)
finally:
    client.meta.events.unregister(
        "before-sign.bedrock-agentcore.InvokeAgentRuntime",
        handler_id,
    )
