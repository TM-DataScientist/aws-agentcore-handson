from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field


class MyCustomToolInput(BaseModel):
    """カスタムツールに渡す入力値の型定義。"""

    # エージェントはこの説明文を見て、どんな値を渡すべきか判断する。
    argument: str = Field(..., description="Description of the argument.")

class MyCustomTool(BaseTool):
    # エージェントがツール一覧の中から選ぶときに参照する名前。
    name: str = "Name of my tool"

    # ツールの用途を具体的に書くほど、エージェントが正しく選びやすくなる。
    description: str = (
        "Clear description for what this tool is useful for, your agent will need this information to use it."
    )

    # ツールの引数として受け付けるスキーマ。
    args_schema: Type[BaseModel] = MyCustomToolInput

    def _run(self, argument: str) -> str:
        # ここに外部 API 呼び出しや独自ロジックを実装する。
        # 返り値の文字列は、そのままエージェントが次の思考材料として使う。
        return "this is an example of a tool output, ignore it and move along."
