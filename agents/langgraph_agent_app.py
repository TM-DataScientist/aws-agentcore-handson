import os
import json
import operator
from typing import TypedDict, Annotated, List, Union
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_aws import ChatBedrock
from langgraph.graph import StateGraph, END
from langchain.agents import create_agent


# --- Bedrock (Claude 3) モデルのセットアップ ---
# Bedrockのクライアントを初期化
# ここでは Claude 3 haikuを使用します
model = ChatBedrock(
    model_id="anthropic.claude-3-haiku-20240307-v1:0", # 使用するモデル
    model_kwargs={"temperature": 0.1},
)


# ツールの定義


@tool
def get_current_datetime() -> str:
    """現在の日時をISOフォーマットで取得します。"""
    import datetime
    return datetime.datetime.now().isoformat()


# ツールをリストにまとめる
tools = [get_current_datetime]


# モデルにツールを「バインド」して、LLMがツールの存在と使い方を
# 認識できるようにします。
model_with_tools = model.bind_tools(tools)


SYSTEM_PROMPT = """
あなたはツールを使えるアシスタントです。
ユーザーが現在日時、今日の日付、今の時間を聞いた場合は、
必ず get_current_datetime ツールを先に呼び出してから回答してください。
質問が日本語でも英語でも同じルールで動作してください。
"""


# 状態の定義


class AgentState(TypedDict):
    """
    エージェントの状態を定義します。
    'messages'キーは、新しいメッセージが追加されるたびにリストに蓄積されます。
    """
    messages: Annotated[List[AnyMessage], operator.add]


# ノードの定義


# 1. モデル呼び出しノード
def call_model(state: AgentState):
    """LLM（Bedrock）を呼び出すノード"""
    print("---[ノード] call_model 実行---")
    messages = state["messages"]
    
    # 状態（会話履歴）をそのままモデルに渡す
    response = model_with_tools.invoke([SystemMessage(content=SYSTEM_PROMPT), *messages])
    
    # モデルの応答（AIMessage）を状態に追加する
    # operator.add が設定されているため、リストに追加される
    return {"messages": [response]}


# 2. ツール実行ノード
def call_tool(state: AgentState):
    """LLMが要求したツールを実行するノード"""
    print("---[ノード] call_tool 実行---")
    
    # 最後のメッセージ（AIからのツール呼び出し要求）を取得
    last_message = state["messages"][-1]
    
    # ツール呼び出し（tool_calls）があるかチェック
    if not last_message.tool_calls:
        # 本来ここには来ないはずだが、念のため
        print("エラー: ツール呼び出しがありません")
        return {}


    # ツールを実行し、結果をリストに格納
    tool_results = []
    tool_map = {t.name: t for t in tools} # ツール名で関数を引けるようにマップを作成


    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        print(f"  > ツール '{tool_name}' を実行します")
        
        if tool_name in tool_map:
            try:
                # ツール（関数）を実行
                tool_output = tool_map[tool_name].invoke(tool_call["args"])
                
                # 結果を ToolMessage 形式で格納
                tool_results.append(
                    ToolMessage(
                        content=str(tool_output), 
                        tool_call_id=tool_call["id"]
                    )
                )
            except Exception as e:
                print(f"ツール実行エラー: {e}")
                tool_results.append(
                    ToolMessage(
                        content=f"Error: {e}", 
                        tool_call_id=tool_call["id"]
                    )
                )
        else:
            print(f"未定義のツール: {tool_name}")
            tool_results.append(
                ToolMessage(
                    content=f"Error: Tool '{tool_name}' not found.", 
                    tool_call_id=tool_call["id"]
                )
            )


    # ツール実行結果（ToolMessageのリスト）を状態に追加する
    return {"messages": tool_results}


# 条件分岐（ルーター）の定義


def should_continue(state):
    last = state["messages"][-1]
    if last.tool_calls:
        return "continue_to_tool"
    return END


# グラフの構築


print("グラフを構築します...")


workflow = StateGraph(AgentState)


# 1. ノードを登録
workflow.add_node("agent", call_model) # モデル呼び出しノード
workflow.add_node("action", call_tool) # ツール実行ノード


# 2. 開始点を設定
workflow.set_entry_point("agent") # 最初に 'agent' ノードから開始


# 3. 条件分岐エッジを設定
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue_to_tool": "action",
        END: END
    }
)


# 4. 通常のエッジを設定 (ループ)
# 'action' ノード（ツール実行）が終わったら、
# 必ず 'agent' ノード（モデル呼び出し）に戻る
workflow.add_edge("action", "agent")


# 5. グラフをコンパイル
app = workflow.compile()


print("グラフのコンパイルが完了しました。")


# エージェントの実行


if __name__ == "__main__":
    print("\n--- エージェント実行開始 ---")
    
    # 最初のユーザー入力
    input_str = input("prompt: ")
    inputs = {"messages": [HumanMessage(content=input_str )]}
    
    # app.stream() を使うと、各ステップ（ノード）の実行結果が順次得られる
    # config={"recursion_limit": 10} は、無限ループを防ぐための実行回数制限
    for output in app.stream(inputs, config={"recursion_limit": 10}):
        # output には、そのステップを終えた時点での「状態」がキーバリューで入る
        # (例: {'agent': {'messages': [...]}} )
        step_name = list(output.keys())[0]
        step_output = output[step_name]
        
        print(f"\n---[ステップ完了] {step_name} ---")
        if "messages" in step_output:
            # 最後のメッセージ（そのステップで追加されたメッセージ）を表示
            last_msg = step_output["messages"][-1]
            if isinstance(last_msg, ToolMessage):
                print(f"  > ツール結果: {last_msg.content}")
            else:
                print(f"  > AI応答/要求: {last_msg.content}")
                if last_msg.tool_calls:
                    print(f"    > ツール呼び出し要求: {last_msg.tool_calls}")


    print("\n--- エージェント実行終了 ---")
    
    # 最終的な状態（全履歴）を取得したい場合
    # final_state = app.invoke(inputs, config={"recursion_limit": 10})
    # print("\n--- 最終回答 ---")
    # print(final_state["messages"][-1].content)
