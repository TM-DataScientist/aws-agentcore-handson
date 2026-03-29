#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from crew_app.crew import CrewApp

# `pysbd` 由来の既知の警告は、このサンプルでは無視して表示をすっきりさせる。
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# このファイルは Crew をローカル実行するための入口。
# 実際のエージェントやタスクの定義は `crew.py` と YAML 側に寄せ、
# ここには「どの入力で、どの実行方法を呼ぶか」だけを書いている。

def run():
    """
    Crew を通常実行する。
    """
    # `topic` と `current_year` は tasks.yaml / agents.yaml の
    # `{topic}` や `{current_year}` に差し込まれる入力値。
    inputs = {
        'topic': 'AI LLMs',
        'current_year': str(datetime.now().year)
    }

    try:
        # Crew の定義を読み込み、最初から最後まで実行する。
        CrewApp().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    指定回数だけ Crew を訓練実行する。
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        # 1 つ目の引数: 繰り返し回数
        # 2 つ目の引数: 学習結果を書き出すファイル名
        CrewApp().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    指定したタスク ID から Crew の実行を再開する。
    """
    try:
        CrewApp().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    評価用 LLM を使って Crew の実行結果をテストする。
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        # 1 つ目の引数: テスト回数
        # 2 つ目の引数: 評価に使うモデル名
        CrewApp().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    外部トリガーから渡された JSON を使って Crew を実行する。
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        # コマンドライン引数として渡された JSON 文字列を辞書へ変換する。
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        # Automation や外部イベント連携では、この payload を参照して
        # タスクの条件分岐や入力補完を行うことが多い。
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        # 通常実行と同じ kickoff を使うが、入力だけトリガー向けに差し替える。
        result = CrewApp().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
