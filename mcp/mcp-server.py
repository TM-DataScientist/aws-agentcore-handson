from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse


# FastMCPを使ってMCPサーバーのインスタンスを作成。
# stateless_http=True でHTTP通信をステートレスモードで利用。
mcp = FastMCP(host="0.0.0.0", stateless_http=True)


# @mcp.tool() デコレータを付けることで「ツール」として登録
@mcp.tool()
def add_numbers(a: int, b: int) -> int:
   """２つの数値を足し合わせます"""
   return a + b


@mcp.tool()
def multiply_numbers(a: int, b: int) -> int:
   """２つの数値を掛け合わせます"""
   return a * b


@mcp.tool()
def greet_user(name: str) -> str:
   """ユーザーに名前で挨拶します"""
   return f"Hello, {name}! Nice to meet you."


if __name__ == "__main__":
   # MCPサーバーを起動し、streamable-httpトランスポートで通信を待ち受ける
   # このファイルを実行すると、サーバーが起動する
   mcp.run(transport="streamable-http")