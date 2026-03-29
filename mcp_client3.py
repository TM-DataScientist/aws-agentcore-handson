import asyncio # 非同期処理を扱うための標準ライブラリ
import json # JSONデータのエンコード・デコードに使用
from mcp import ClientSession # MCPセッション管理のためのクラス
from mcp.client.streamable_http import streamablehttp_client # ストリーミングHTTPクライアント


# グローバル変数として、呼び出すツール名と引数を初期化
tool_name = '' 
tool_args = {}


def get_input():
    # グローバル変数を宣言、関数内で値を更新できるようにする
    global tool_name, tool_args
    # ユーザーに実行したいツールの番号を入力させる
    func_num = int(input('ツール番号(1:add, 2:multiply, 3:greet): '))


    # --- ツール1: 数値の加算 (add_numbers) ---
    def process_1():
        # グローバル変数を更新
        global tool_name, tool_args
        tool_name = 'add_numbers'
        # ユーザーから加算する2つの数値を取得
        a = int(input('a: '))
        b = int(input('b: '))
        # ツール引数を辞書として設定
        tool_args = {'a': a, 'b': b}


    # --- ツール2: 数値の乗算 (multiply_numbers) ---
    def process_2():
        # グローバル変数を更新
        global tool_name, tool_args
        tool_name = 'multiply_numbers'
        # ユーザーから乗算する2つの数値を取得
        a = int(input('a: '))
        b = int(input('b: '))
        # ツール引数を辞書として設定
        tool_args = {'a': a, 'b': b}


    # --- ツール3: ユーザーへの挨拶 (greet_user) ---
    def process_3():
        # グローバル変数を更新
        global tool_name, tool_args
        tool_name = 'greet_user'
        # ユーザーから名前を取得
        name = input('name: ')
        # ツール引数を辞書として設定
        tool_args = {'name': name}


    # 入力された番号に対応する関数を格納した辞書
    process_dict = {
        1: process_1,
        2: process_2,
        3: process_3
    }


    # 辞書から対応する関数を取得して実行
    process_dict.get(func_num, lambda: print("値は1, 2, 3以外です"))()


async def main():
    # get_input()で設定されたグローバル変数を使用
    global tool_name, tool_args
    # MCPサーバーのエンドポイントURL
    mcp_url = "http://localhost:8000/mcp"
    # HTTPヘッダー（今回は空）
    headers = {}


    # ストリーミングHTTPクライアントでサーバーと接続
    async with streamablehttp_client(
        mcp_url, 
        headers, 
        timeout=120, 
        terminate_on_close=False
    ) as (
        read_stream, # サーバーからのデータ読み込みストリーム
        write_stream, # サーバーへのデータ書き込みストリーム
        _, # 未使用の変数
    ):
        # 取得したストリームを使ってMCPセッションを開始
        async with ClientSession(read_stream, write_stream) as session:
            # セッションを初期化し、接続を確立
            await session.initialize()
            print("MCP Session Initialized. (セッション確立)")


            # ツールを呼び出す処理
            print(f"\n--- Calling Tool: '{tool_name}' with args: {tool_args} ---")
            try:
                # session.call_tool() でツールをリモート実行し、結果を受け取ります。
                tool_call_result = await session.call_tool(tool_name, tool_args)
            
                print(f"\n--- Tool Call Result ---")
                # ツール呼び出し結果から 'structuredContent' 内の 'result' を表示
                print(f"呼び出し結果: {tool_call_result.structuredContent['result']}")
                print("------------------------")
            except Exception as e:
                # ツール呼び出し中にエラーが発生した場合の処理
                print(f"Error calling tool '{tool_name}': {e}")


# ユーザーからの入力でツール名と引数を設定
get_input()
# 非同期ランタイムを開始し、mainコルーチンを実行
asyncio.run(main())