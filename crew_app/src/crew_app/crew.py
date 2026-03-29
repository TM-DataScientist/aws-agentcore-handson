from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

# `@CrewBase` を付けると、同名の YAML 設定を読み込みつつ
# エージェント・タスク・Crew を宣言的に組み立てられる。
# 実行前後に処理を差し込みたい場合は `@before_kickoff` / `@after_kickoff`
# を使う構成にも拡張できる。

@CrewBase
class CrewApp():
    """CrewApp のエージェント構成と実行フローをまとめるクラス。"""

    # `@agent` / `@task` で作られたオブジェクトが自動でここに集約される。
    agents: list[BaseAgent]
    tasks: list[Task]

    # エージェントの人格や役割は `config/agents.yaml` で定義する。
    # ここでは「どの設定を使って Agent を作るか」だけを記述する。
    @agent
    def researcher(self) -> Agent:
        return Agent(
            # `researcher` キーに対応する YAML 設定を読み込む。
            config=self.agents_config['researcher'], # type: ignore[index]
            verbose=True
        )

    # レポート作成担当のエージェント。
    # 前段の調査結果を受けて、読みやすい文章へまとめる役割を持つ。
    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'], # type: ignore[index]
            verbose=True
        )

    # 1 つ目のタスク。トピックに関する調査を担当する。
    @task
    def research_task(self) -> Task:
        return Task(
            # `research_task` の説明文や期待出力は tasks.yaml 側で管理する。
            config=self.tasks_config['research_task'], # type: ignore[index]
        )

    # 2 つ目のタスク。調査結果をレポートへ整形し、ファイルにも保存する。
    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'], # type: ignore[index]
            # 実行結果を Markdown ファイルとして保存する。
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Crew 全体の実行順序と共通設定を返す。"""

        return Crew(
            # 上の `@agent` / `@task` で定義した内容が自動でここへ入る。
            agents=self.agents,
            tasks=self.tasks,
            # 今回は research -> report の順に 1 本ずつ実行する。
            process=Process.sequential,
            verbose=True,
            # 管理役エージェントを立てる構成にしたい場合は
            # `Process.hierarchical` へ切り替える余地がある。
        )
