import boto3
import json
import os
from bedrock_agentcore.memory import MemoryClient


memory = MemoryClient(region_name="us-east-1")


# 既存のメモリを指定して使う。
# 実際の環境では BEDROCK_AGENTCORE_MEMORY_ID を設定してから実行する。
memory_id = os.getenv("BEDROCK_AGENTCORE_MEMORY_ID", "")
if not memory_id:
    raise ValueError("BEDROCK_AGENTCORE_MEMORY_ID environment variable is required.")
print(f'使用するメモリID: {memory_id}.')


# --- 最初のイベントの作成（ユーザーの元のコード） ---
print("最初のイベントを作成中...")


session_id = 'OrderSupportSession1-abcdefg1234567890' # セッションID
actor_id = 'User99' # アクタID


memory.create_event(
    memory_id=memory_id,
    actor_id=actor_id,
    session_id=session_id,
    messages=[
        ("こんにちは。注文番号12345で問題が起こったのですが。", "USER"),
        ("申し訳ございません。ご注文を確認させていただきます。", "ASSISTANT"),
        ("lookup_order(order_id='12345')", "TOOL"),
        ("ご注文は3日前に発送されましたね。具体的にどのような問題が発生していますか？", "ASSISTANT"),
        ("実はその前にメールアドレスも変更したいのですが。", "USER"),
        (
            "もちろんです！まずはメールアドレスの更新を行いましょう。新しいメールアドレスを教えて下さい。",
            "ASSISTANT",
        ),
        ("newemail@example.com", "USER"),
        ("update_customer_email(old='old@example.com', new='newemail@example.com')", "TOOL"),
        ("メールが更新されました！さて、ご注文に関する問題についてお伺いします。", "ASSISTANT"),
        ("荷物が破損して届きました", "USER"),
        ("大変申し訳ございません。お手数ですが商品をこちらにご返送いただけば返金の手続きをいたします。", "ASSISTANT")
    ],
)
print("最初のイベントがメモリに記録されました。")
print("---")


# ユーザーの新しい入力とその応答をシミュレートし、新しいイベントを作成


# ユーザーからの新しい入力
new_user_message = input("prompt: ")


# 短期記憶の取得
events = memory.list_events(
    memory_id=memory_id,
    actor_id=actor_id,
    session_id=session_id
)


# content を抽出
event_texts = []
event = events[0]
f = False
c = ['[USER]: ','[ASSISTANT]: ']
for ev in event['payload']:
    content = ev['conversational']['content']['text']
    event_texts.append(c[f] + content)
    f = not f
memory_text = "\n".join(event_texts)


prompt = f"""
以下は最近のやり取りです:
{memory_text}


これらの情報から回答してください。


[USER]: {new_user_message}
[ASSISTANT]: 
"""


# エージェントの作成
boto3_client = boto3.client('bedrock-agentcore', region_name='us-east-1')


# エージェントからの応答
agent_runtime_arn = os.getenv("BEDROCK_AGENT_RUNTIME_ARN", "")
if not agent_runtime_arn:
    raise ValueError("BEDROCK_AGENT_RUNTIME_ARN environment variable is required.")

new_assistant_response = boto3_client.invoke_agent_runtime(
    agentRuntimeArn=agent_runtime_arn,
    runtimeSessionId=session_id, 
    payload=json.dumps({"prompt": prompt}),
    qualifier="DEFAULT"
)
response_body = new_assistant_response['response'].read()
response_data = json.loads(response_body)
response_text = response_data['result']['content'][0]['text']


print(f"ユーザー入力: {new_user_message}")
print(f"エージェント応答: {response_text}")
