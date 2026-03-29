from bedrock_agentcore.tools.code_interpreter_client import CodeInterpreter
import json


# Configureクライアントを作成し利用開始する
code_client = CodeInterpreter('us-east-1')
code_client.start()


# コードを実行する
response = code_client.invoke("executeCode", {
  "language": "python", 
  "code": 'print("Hello World!!!")'
})


# 応答を処理し出力する
for event in response["stream"]:
  print(json.dumps(event["result"], indent=2))


# クライアントを停止する 
code_client.stop()