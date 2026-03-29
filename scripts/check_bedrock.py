import boto3
import json


# Boto3クライアントを作成するリージョンを指定
# aws configure で設定したリージョンと合わせる
TARGET_REGION = "us-east-1" 


print(f"Boto3を使って、リージョン '{TARGET_REGION}' のBedrockに接続テストを行います...")


try:
    # Bedrockの「管理用」クライアントを作成
    # (モデルを呼び出すときは 'bedrock-runtime' を使います)
    bedrock_client = boto3.client(
        service_name='bedrock', 
        region_name=
        TARGET_REGION
    )


    # 利用可能な基盤モデルのリストを取得してみる
    response = bedrock_client.list_foundation_models()


    print("\n[成功] Boto3のセットアップ成功。Bedrockに接続できました。")


    # 利用可能なモデルが多すぎるため、Anthropic (Claude) のモデルだけを抜粋
    claude_models = [
        model['modelId'] for model in response['modelSummaries'] 
        if 'anthropic.claude' in model['modelId']
    ]


    print(f"\nリージョン '{TARGET_REGION}' で利用可能な Claude モデル (一部):")
    if claude_models:
        for model_id in claude_models:
            print(f"- {model_id}")
    else:
        print("Claude モデルが見つかりません。")


except Exception as e:
    print(f"\n[エラー] 接続に失敗しました: {e}")
    print("\n[トラブルシューティングのヒント]")
    print("1. IAMユーザーに 'AmazonBedrockFullAccess' ポリシーがアタッチされていますか？")
    print(f"2. 'aws configure' で設定したリージョンは '{TARGET_REGION}' になっていますか？")
    print("3. 'aws sts get-caller-identity' コマンドは正常に実行できますか？")
    print("4. (次項) Bedrockの「モデルアクセス」は有効化されていますか？")
