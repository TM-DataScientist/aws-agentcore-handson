import boto3
import json
import uuid


# 設定が必要な項目


# 1. リージョン名
#    エージェントを作成したリージョン (例: 'us-east-1')
TARGET_REGION = 'us-east-1' 


# 2. エージェントID (Agent ID)
#    Bedrockコンソールの MyFirstAgent 概要ページで確認
#    例: 'ABC123DEF4'
AGENT_ID = 'SNZ7I5KBC6'  # エージェントIDを指定


# 3. エージェント・エイリアスID (Agent Alias ID)
#    概要ページ、または「Aliases」タブで確認
AGENT_ALIAS_ID = '7CG26UNBJ2' # エイリアスIDを指定


# 設定ここまで


def chat_with_agent(client, agent_id, alias_id, session_id, prompt_text):
    """
    Bedrockエージェントと対話し、応答をストリーミングで受け取る関数
    """
    
    print(f"\n[ユーザー]: {prompt_text}")
    print("[エージェント]: ", end="", flush=True)
    
    try:
        # エージェントを呼び出す (InvokeAgent)
        response = client.invoke_agent(
            agentId=agent_id,
            agentAliasId=alias_id,
            sessionId=session_id,
            inputText=prompt_text,
            enableTrace=False # トレース情報が不要な場合はFalse
        )
        
        full_response = ""
        
        # エージェントの応答は「ストリーミング」形式で返ってくる
        if 'completion' in response:
            for event in response['completion']:
                if 'chunk' in event:
                    # 'chunk' にAIの回答の「断片」が bytes 形式で入っている
                    chunk = event['chunk']
                    decoded_chunk = chunk['bytes'].decode('utf-8')
                    
                    # 断片をコンソールに即時出力 (ストリーミング表示)
                    print(decoded_chunk, end="", flush=True)
                    
                    full_response += decoded_chunk
        
        print() # 最後に改行
        return full_response


    except Exception as e:
        print(f"\n[エラー]: {e}")
        return None


def main():
    """
    メインの実行関数
    """
    # AGENT_ID と AGENT_ALIAS_ID が設定されているかチェック
    if AGENT_ID == 'YOUR_AGENT_ID' or \
          AGENT_ALIAS_ID == 'YOUR_AGENT_ALIAS_ID':
        print("[エラー] AGENT_ID と AGENT_ALIAS_ID を、")
        print("        Bedrockコンソールで確認した値に書き換えてください。")
        return


    # Bedrockエージェントの「実行(Runtime)」用クライアントを作成
    try:
        client = boto3.client(
            'bedrock-agent-runtime', 
            region_name=TARGET_REGION
        )
    except Exception as e:
        print(f"[エラー] Boto3クライアントの作成に失敗しました: {e}")
        print("AWSの認証情報が正しく設定されているか確認してください。")
        return


    # セッションID (Session ID)
    # 会話の履歴を管理するためのID。
    # このIDが同じである限り、エージェントは過去の会話を記憶します。
    session_id = str(uuid.uuid4())
    print(f"セッションID: {session_id} でエージェントとの会話を開始します。")
    print("終了するには 'exit' または 'quit' と入力してください。")


    # 対話ループ
    while True:
        try:
            user_input = input("\n[ユーザー]: ")
            if user_input.lower() in ['exit', 'quit']:
                print("会話を終了します。")
                break
            
            chat_with_agent(client, AGENT_ID, AGENT_ALIAS_ID, session_id, user_input)
            
        except KeyboardInterrupt:
            print("\n会話を中断しました。")
            break


# このファイルが直接実行された時だけ main() を呼び出す
if __name__ == "__main__":
    main()