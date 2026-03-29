import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
 mcp_url = "http://localhost:8000/mcp"
 headers = {}


 # streamablehttp_clientを使ってサーバーに接続します。
 async with streamablehttp_client(mcp_url, headers, timeout=120, terminate_on_close=False) as (
   read_stream,
   write_stream,
   _,
 ):
   # 接続ストリームからClientSessionを作成します。
   async with ClientSession(read_stream, write_stream) as session:
     await session.initialize()
     print("MCP Session Initialized. (セッション確立)")
    
     # session.list_tools()を呼び出し、サーバー上の全ツールを取得します。
     tool_result = await session.list_tools()
     print("\n--- 利用可能なツール一覧 ---")
     for tool in tool_result.tools:
       print(f"名前: {tool.name}, 説明: {tool.description}")
     print("--------------------------")


asyncio.run(main())