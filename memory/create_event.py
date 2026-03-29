from bedrock_agentcore.memory import MemoryClient


client = MemoryClient(region_name="us-east-1")


memory = client.list_memories()[0] # 最初のメモリを取り出す


response = client.create_event(
    memory_id=memory.get("id"), # list_memoriesから得たメモリのID
    actor_id="User99",  # アクターのID（ここではユーザーを識別する）
    session_id="OrderSupportSession1", #リクエスト/会話のID。
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
    ],
)


print("Created event: ", response['eventId']) # イベントIDの表示
print("Event timestamp: ", response['eventTimestamp']) # 作成時刻の表示