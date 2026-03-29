"""
CLIから都市名を受け取り、日本語でレポートを生成。
_geocodeで日本語名を英語に変換し、API検索が失敗しないようにする。
"""
# 必要なライブラリのインポート
from dataclasses import dataclass, field
from datetime import datetime
import os
from pathlib import Path
import requests # 外部APIへのHTTPリクエストに使用
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup # (未使用だが元のコードに含まれていたためそのまま) HTML解析用
import sys # コマンドライン引数処理用
import json # JSONデータの処理用
from dotenv import load_dotenv


# `crew_app/.env` を読み込み、各 API キーを環境変数から参照できるようにする。
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


# 【エージェントの定義】
# CrewAIにおける「ツール」または「エージェントが使用する機能」に相当するクラス群


@dataclass
class WeatherAgent:
    """Open-Meteo APIから天気情報を取得するエージェント"""
    base_url: str = "https://api.open-meteo.com/v1/forecast" # 天気予報APIのベースURL


    def fetch(self, lat: float, lon: float, timezone: str = "UTC") -> Dict[str, Any]:
        """指定された緯度・経度の天気情報を取得する"""
        try:
            # APIリクエストのパラメータを設定
            params = {
                "latitude": lat,
                "longitude": lon,
                "current_weather": True, # 現在の天気を取得
                "hourly": "temperature_2m,precipitation,weathercode", #気温 降水 天気コード取得
                "timezone": timezone, # タイムゾーン
            }
            # APIへGETリクエストを送信
            resp = requests.get(self.base_url, params=params, timeout=10)
            resp.raise_for_status() # HTTPエラーが発生した場合、例外を発生
            return resp.json() # 成功した場合、JSONレスポンスを返す
        except Exception as e:
            # 取得失敗時、空の辞書を返す
            print(f"WeatherAgent error: {e}")
            return {}


@dataclass
class WikiAgent:
    """Wikipedia APIから記事の要約を取得するエージェント"""
    base_url: str = "https://ja.wikipedia.org/api/rest_v1/page/summary/" # WikipediaのAPI
    headers = {"User-Agent": "Mozilla/5.0"} # リクエストのUser-Agent


    def fetch_summary(self, title: str) -> Dict[str, Any]:
        """指定されたタイトル（都市名など）のWikipedia要約を取得する"""
        try:
            safe_title = title.replace(" ", "_")
            # 特定の主要都市以外の場合、検索効率のために「県」を追加する
            if safe_title not in ['東京','京都','大阪','名古屋','北海道']:
                safe_title += '県'
            
            url = self.base_url + safe_title # リクエストURLを構築
            resp = requests.get(url, headers=self.headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            # 取得失敗時、空の辞書を返す
            print(f"WikiAgent error: {e}")
            return {}


@dataclass
class PlacesAgent:
    """Hotpepper API を利用して指定都市の飲食店情報を取得するエージェント"""
    # API キーはコードへ直書きせず、`.env` の `HOTPEPPER_API_KEY` から読む。
    hotpepper_key: str = field(default_factory=lambda: os.getenv("HOTPEPPER_API_KEY", ""))
    large_area_url: str = "http://webservice.recruit.co.jp/hotpepper/large_area/v1/"
    shop_search_url: str = "http://webservice.recruit.co.jp/hotpepper/gourmet/v1/"


    def get_area_code(self, city: str) -> Optional[str]:
        """都市名を含む large_area コードを Hotpepper API から取得する"""
        if not self.hotpepper_key:
            print("PlacesAgent area code error: HOTPEPPER_API_KEY is not set")
            return None

        try:
            params = {"key": self.hotpepper_key, "format": "json"}
            # 大エリア一覧を取得
            resp = requests.get(self.large_area_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            # 取得したエリア一覧から、都市名を含むエリアコードを検索
            for area in data.get("results", {}).get("large_area", []):
                if city in area.get("name", ""):
                    return area.get("code")
        except Exception as e:
            print(f"PlacesAgent area code error: {e}")
            pass
        return None


    def search(self, city: str, limit: int = 10) -> List[Dict[str, Any]]:
        """都市名に対応するエリアコードを使って飲食店情報を検索する"""
        if not self.hotpepper_key:
            print("PlacesAgent search error: HOTPEPPER_API_KEY is not set")
            return []

        area_code = self.get_area_code(city)
        if not area_code:
            return [] # エリアコードが取得できなければ空リストを返す
            
        try:
            # 飲食店検索のパラメータを設定
            params = {
                "key": self.hotpepper_key,
                "format": "json",
                "large_area": area_code, # 取得したエリアコードを使用
                "count": limit # 取得件数
            }
            # 飲食店検索APIへリクエストを送信
            resp = requests.get(self.shop_search_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            shops = []
            # 必要な情報（店舗名とPC用URL）を抽出
            for shop in data.get("results", {}).get("shop", []):
                shops.append({
                    "title": shop.get("name"),
                    "url": shop.get("urls", {}).get("pc")
                })
            return shops
        except Exception as e:
            print(f"PlacesAgent search error: {e}")
            return []


@dataclass
class ReportAgent:
    """収集した情報を統合し、最終的なレポート（Markdown形式）を生成するエージェント"""


    def getWmoWeather(self, code: int):
      """"""
      wmo = {
          0: "晴れ", 1: "概ね晴れ", 2: "所により曇り",
          3: "曇り", 45: "霧", 48: "霧氷", 51: "霧雨",
          53: "霧雨", 55: "霧雨", 56: "着氷性の霧雨",
          57: "着氷性の霧雨", 61: "雨", 63: "雨", 65: "雨",
          66: "着氷性の雨", 67: "着氷性の雨",
          71: "雪", 73: "雪", 75: "雪", 77: "霧雪",
          80: "にわか雨", 81: "にわか雨", 82: "にわか雨",
          85: "にわか雪", 86: "にわか雪",
          95: "雷雨", 96: "雷雨", 99: "雷雨",
      }
      return wmo.get(code, '不明')


    def assemble(self, city: str, weather: Dict[str, Any], wiki: Dict[str, Any], places: List[Dict[str, Any]]) -> str:
        """収集したデータからMarkdown形式のレポートを作成する"""
        # レポートのヘッダー情報を作成
        lines = [f"# {city} のレポート", "", f"生成日時: {datetime.utcnow().isoformat()} UTC", ""]
        
        # --- 天気情報セクション ---
        lines.append("## 天気情報")
        cw = weather.get("current_weather")
        code = int(cw.get('weathercode', -1))
        
        lines.append(f"- 現在の天気: {self.getWmoWeather(code)}")
        lines.append(f"- 現在の気温: {cw.get('temperature', 'N/A')} °C")
        lines.append(f"- 風速: {cw.get('windspeed', 'N/A')} m/s")
        lines.append("")


        # --- Wikipedia情報セクション ---
        lines.append("## その場所について（Wikipedia）")
        title = wiki.get("title")
        extract = wiki.get("extract")
        if title and extract:
            lines.append(f"**{title}**")
            lines.append("")
            # 要約文が長すぎる場合、1200文字で切り詰める
            excerpt = extract[:1200] + ("..." if len(extract) > 1200 else "")
            lines.append(excerpt)
        else:
            lines.append("Wikipedia の要約が見つかりません。")
        lines.append("")


        # --- 飲食店情報セクション ---
        lines.append("## 飲食店情報 (Hotpepper の検索結果)")
        if places:
            for p in places:
                lines.append(f"- [{p.get('title', '不明')}]({p.get('url', '#')})")
        else:
            lines.append("見つかりませんでした。")


        return "\n".join(lines)


# 【Crewの定義】
# 複数のエージェント（機能）を連携させ、一連のタスクを管理・実行するクラス


class TravelReportCrew:
    """旅行レポート生成のためのタスクとエージェントを管理するクルー（Crew）クラス"""
    def __init__(self):
        # 各エージェントのインスタンス化
        self.weather_agent = WeatherAgent()
        self.wiki_agent = WikiAgent()
        self.places_agent = PlacesAgent()
        self.report_agent = ReportAgent()
        # 各タスクの結果を保持するための変数
        self._weather: Dict[str, Any] = {}
        self._wiki: Dict[str, Any] = {}
        self._places: List[Dict[str, Any]] = []


    def _geocode(self, city: str) -> Optional[Dict[str, Any]]:
        """都市名を緯度・経度に変換するジオコーディング処理"""
        # ジオコーディングAPIの引数に合わせるための日本語-英語変換マップ
        # 日本の全47都道府県の日本語名とその英語表記（ローマ字）をマッピングした辞書
        jp_to_en = {
            "北海道": "Hokkaido", "青森": "Aomori", "岩手": "Iwate",
            "宮城": "Miyagi", "秋田": "Akita", "山形": "Yamagata",
            "福島": "Fukushima", "茨城": "Ibaraki", "栃木": "Tochigi",
            "群馬": "Gunma", "埼玉": "Saitama", "千葉": "Chiba",
            "東京": "Tokyo", "神奈川": "Kanagawa", "新潟": "Niigata",
            "富山": "Toyama", "石川": "Ishikawa", "福井": "Fukui",
            "山梨": "Yamanashi", "長野": "Nagano", "岐阜": "Gifu",
            "静岡": "Shizuoka", "愛知": "Aichi", "三重": "Mie",
            "滋賀": "Shiga", "京都": "Kyoto", "大阪": "Osaka",
            "兵庫": "Hyogo", "奈良": "Nara", "和歌山": "Wakayama",
            "鳥取": "Tottori", "島根": "Shimane", "岡山": "Okayama",
            "広島": "Hiroshima", "山口": "Yamaguchi", "徳島": "Tokushima",
            "香川": "Kagawa", "愛媛": "Ehime", "高知": "Kochi",
            "福岡": "Fukuoka", "佐賀": "Saga", "長崎": "Nagasaki",
            "熊本": "Kumamoto", "大分": "Oita", "宮崎": "Miyazaki",
            "鹿児島": "Kagoshima", "沖縄": "Okinawa"
        }
        city_en = jp_to_en.get(city, city) # 変換マップにあれば英語名、なければそのまま都市名
        try:
            # Open-MeteoのジオコーディングAPIを使用
            resp = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city_en}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            # 最初の検索結果を返す
            if data.get("results"):
                return data["results"][0]
        except Exception as e:
            print(f"Geocoding error: {e}")
            pass
        return None


    def fetch_weather_task(self, city: str) -> None:
        """天気情報を取得するタスク"""
        print("fetch_weather_task: 実行")
        loc = self._geocode(city) # ジオコーディングを実行
        if not loc:
            self._weather = {}
            print("fetch_weather_task: 失敗（ジオコーディングできず）")
            return
        # ジオコーディング結果を使って天気情報を取得し、結果を内部変数に保存
        self._weather = self.weather_agent.fetch(loc.get("latitude"), loc.get("longitude"), loc.get("timezone", "UTC"))
        print("fetch_weather_task: 終了")
        
    def fetch_wikipedia_task(self, city: str) -> None:
        """Wikipediaの要約を取得するタスク"""
        print("fetch_wikipedia_task: 実行")
        # WikiAgentを使用して要約を取得し、結果を内部変数に保存
        self._wiki = self.wiki_agent.fetch_summary(city)
        print("fetch_wikipedia_task: 終了")


    def fetch_places_task(self, city: str) -> None:
        """飲食店情報を取得するタスク"""
        print("fetch_places_task: 実行")
        # PlacesAgentを使用して飲食店情報を検索し、結果を内部変数に保存
        restaurants = self.places_agent.search(f"{city}", limit=10)
        self._places = restaurants
        print("fetch_places_task: 終了")


    def write_report_task(self, city: str, filename: str = "travel_report.md") -> None:
        """収集したデータからレポートを作成し、ファイルに書き出すタスク"""
        print("write_report_task: 実行")
        # ReportAgentを使用して最終レポート（Markdown文字列）を生成
        report_md = self.report_agent.assemble(city, self._weather, self._wiki, self._places)
        # ファイルへの書き出し
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_md)
        print("write_report_task: 終了")
        print("========== レポート結果 ==========")
        print(report_md)
        print("========== ここまで ==========\n")
      
    def run(self, city: str, output: str = "travel_report.md") -> str:
        """全てのタスクを実行するメインのシーケンス"""
        # 各タスクを順次実行（CrewAI本来は並列実行も可能）
        self.fetch_weather_task(city)
        self.fetch_wikipedia_task(city)
        self.fetch_places_task(city)
        self.write_report_task(city, output)
        print("Crew finished. Report saved to:", output)
        return output


# 【CLIからの実行】
# スクリプトが直接実行された場合の処理


if __name__ == "__main__":
    # コマンドライン引数のチェック
    if len(sys.argv) < 3 or sys.argv[1] != "run":
        print("Usage: python travel_report_crew.py run <都市名>")
        sys.exit(1)
        
    city_name = sys.argv[2] # 2番目の引数を都市名として取得
    
    # Crewのインスタンス化と実行
    crew = TravelReportCrew()
    crew.run(city=city_name)
