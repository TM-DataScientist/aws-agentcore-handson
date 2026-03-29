import boto3
import json


client = boto3.client('bedrock-agentcore', region_name='us-east-1')


response = client.invoke_code_interpreter(
    codeInterpreterIdentifier='aws.codeinterpreter.v1',
    name='executeCode',
    arguments={
        'code': '''
print("Hello, world!")
total = 0
for i in range(1,101):
    total = total + i
print(f'total: {total}.')
        ''',
        'language': 'python'
    }
)


print("=== Code Interpreter Output ===")


for event in response['stream']:
    # event は以下のような辞書になる
    print(event['result']['content'][0]['text'])


    if "error" in event:
        # 実行時エラー
        print("[ERROR]", event["error"])