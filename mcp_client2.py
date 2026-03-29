import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    mcp_url = "http://localhost:8000/mcp"
    headers = {}

    async with streamablehttp_client(
        mcp_url,
        headers,
        timeout=120,
        terminate_on_close=False,
    ) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("MCP Session Initialized. (セッション確立)")

            # ツールを呼び出す例
            tool_name = "add_numbers"  # 呼び出したいツールの名前
            tool_args = {
                "a": 10,
                "b": 5,
            }  # ツールに渡す引数（辞書形式）

            print(f"\n--- Calling Tool: '{tool_name}' with args: {tool_args} ---")
            try:
                # session.call_tool() でツールをリモート実行し、結果を受け取ります。
                tool_call_result = await session.call_tool(tool_name, tool_args)

                print(f"\n--- Tool Call Result ---")

                # CallToolResult では、結果は structuredContent か content に入ります。
                if (
                    tool_call_result.structuredContent
                    and "result" in tool_call_result.structuredContent
                ):
                    result_value = tool_call_result.structuredContent["result"]
                elif tool_call_result.content:
                    result_value = tool_call_result.content[0].text
                else:
                    result_value = "結果を取得できませんでした。"

                print(f"呼び出し結果: {result_value}")
                print("------------------------")
            except Exception as e:
                print(f"Error calling tool '{tool_name}': {e}")


asyncio.run(main())
