"""
travel_report_crew.py から TravelReportCrew を実行するためのCLIラッパー


使用例:
python run_travel_crew.py run 東京
python run_travel_crew.py run_with_payload '{"city": "東京"}'
"""
# 必要なライブラリのインポート
import sys # コマンドライン引数を扱うためのモジュール
import json # JSONデータを解析するためのモジュール
# 前のファイルで定義されたクルー（Crew）クラスをインポート
# （このファイルを実行するには、`travel_report_crew.py`が同じディレクトリにある必要があります）
from travel_report_crew import TravelReportCrew


def usage_and_exit():
    """使用法メッセージを表示し、スクリプトを終了する"""
    print("Usage:")
    print("  python run_travel_crew.py run <CityName> [output_filename]")
    print("  python run_travel_crew.py run_with_payload '<json-payload>'")
    sys.exit(1)


# スクリプトが直接実行された場合のメイン処理
if __name__ == "__main__":
    # 引数が1つ（スクリプト名のみ）の場合、使用法を表示して終了
    if len(sys.argv) < 2:
        usage_and_exit()


    cmd = sys.argv[1] # 最初の引数（コマンド）を取得


    crew = TravelReportCrew() # TravelReportCrewのインスタンスを生成


    # --- "run" コマンドの処理 ---
    if cmd == "run":
        # 都市名が指定されているかチェック
        if len(sys.argv) < 3:
            usage_and_exit()
        
        city = sys.argv[2] # 2番目の引数を都市名として取得
        
        # 3番目の引数があればそれを出力ファイル名に、なければデフォルト値を使用
        output = sys.argv[3] if len(sys.argv) > 3 else "travel_report.md"
        
        # クルーを実行
        crew.run(city=city, output=output)


    # --- "run_with_payload" コマンドの処理 ---
    elif cmd == "run_with_payload":
        # JSONペイロードが指定されているかチェック
        if len(sys.argv) < 3:
            usage_and_exit()
            
        try:
            # 2番目の引数をJSON文字列として解析
            payload = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            # JSON解析エラーが発生した場合
            print("Invalid JSON payload")
            sys.exit(1)
            
        # ペイロードから 'city' または 'topic' キーの値を取得
        city = payload.get("city") or payload.get("topic") or ""
        
        # 都市名が取得できなかった場合
        if not city:
            print("Payload must contain 'city' or 'topic'")
            sys.exit(1)
            
        # クルーを実行（この実行方法では、出力ファイル名はデフォルト値になる）
        crew.run(city=city)


    # --- 未知のコマンドの場合の処理 ---
    else:
        usage_and_exit()