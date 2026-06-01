# -*- coding: utf-8 -*-
"""
⛰️ 百名山 計画＆フォトマップ
スマホのホーム画面に追加して使う、日本百名山の登山計画・登頂記録アプリ。

実行: streamlit run app.py
必要ライブラリ: streamlit folium streamlit-folium pandas requests
"""

import os
import csv
import base64
import html
import math
from datetime import date, datetime

import streamlit as st
import folium
from streamlit_folium import st_folium

# ============================================================
# 基本設定
# ============================================================
st.set_page_config(
    page_title="百名山アプリ",
    page_icon="⛰️",
    layout="centered",                 # スマホの縦長画面に合わせる
    initial_sidebar_state="collapsed",
)

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTO_DIR = os.path.join(DATA_DIR, "photos")
CSV_PATH = os.path.join(DATA_DIR, "records.csv")
os.makedirs(PHOTO_DIR, exist_ok=True)

# 天気を本物にしたいときは True（要ネット接続 / Open-Meteo・APIキー不要）
USE_REAL_WEATHER_DEFAULT = False

LEVEL_EMOJI = {"初級": "🟢初級", "中級": "🟡中級", "上級": "🔴上級"}

# ============================================================
# スマホ特化 CSS（手袋でも押しやすい大きめUI・縦一列）
# ============================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700;900&display=swap');

    /* やさしいクリーム〜ラベンダーの空 */
    .stApp, [data-testid="stAppViewContainer"] {
        background: linear-gradient(175deg,#fdf6f0 0%,#fce4ec 30%,#f3e5f5 60%,#e8eaf6 100%) fixed;
    }
    .block-container {padding-top: 1rem; padding-bottom: 4.5rem; max-width: 560px;}
    html, body, [class*="css"] {
        font-family:'Zen Maru Gothic','Hiragino Maru Gothic','Yu Gothic',sans-serif;
    }

    /* ボタン：さくらピンクのやわらかグラデ */
    .stButton > button, .stFormSubmitButton > button {
        width: 100%;
        padding: 0.95rem 0.6rem;
        font-size: 1.08rem;
        font-weight: 900;
        color: #fff !important;
        border: none;
        border-radius: 20px;
        margin-bottom: 0.45rem;
        background: linear-gradient(135deg,#f48fb1 0%,#ce93d8 50%,#9fa8da 100%);
        box-shadow: 0 6px 20px rgba(206,147,216,0.35);
        letter-spacing: 0.5px;
        transition: transform .1s ease, box-shadow .15s ease, filter .15s ease;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover {
        transform: translateY(-2px) scale(1.01);
        box-shadow: 0 10px 26px rgba(206,147,216,0.45);
        filter: brightness(1.06);
        color:#fff !important;
    }
    .stButton > button:active, .stFormSubmitButton > button:active {transform: scale(0.97);}

    /* 入力まわり */
    .stSelectbox label, .stRadio label, .stTextInput label,
    .stDateInput label, .stFileUploader label {font-size:1.0rem; font-weight:700; color:#8e6280;}
    div[data-baseweb="select"] > div {min-height:50px; font-size:1.0rem; border-radius:14px;
        border-color:#e1bee7 !important;}

    /* タブ：パステルの丸タブ */
    .stTabs [data-baseweb="tab-list"] {gap:5px; background:rgba(255,255,255,.6);
        padding:6px; border-radius:18px;}
    .stTabs [data-baseweb="tab"] {font-size:0.96rem; font-weight:900; padding:0.55rem 0.4rem;
        border-radius:14px; color:#ab68a8;}
    .stTabs [aria-selected="true"] {
        background:linear-gradient(135deg,#f48fb1,#ce93d8);
        color:#fff !important;
    }

    /* ===== ヒーロー ===== */
    .hero {position:relative; overflow:hidden; border-radius:26px; padding:20px 18px 16px;
        margin-bottom:12px; color:#fff;
        background:linear-gradient(135deg,#ad5389 0%,#3c1053 100%);
        box-shadow:0 14px 34px rgba(60,16,83,.3);}
    .hero::before {content:'🌸'; position:absolute; top:-8px; right:6px;
        font-size:4rem; opacity:.15; transform:rotate(18deg);}
    .hero h1 {font-size:1.45rem; font-weight:900; margin:0; letter-spacing:1px;}
    .hero .sub {font-size:0.88rem; opacity:.85; margin-top:3px;}
    .hero-row {display:flex; align-items:center; gap:16px; margin-top:12px;}
    .ring {width:100px; height:100px; border-radius:50%; flex:0 0 auto;
        display:flex; align-items:center; justify-content:center;
        box-shadow:0 0 0 6px rgba(255,255,255,.1) inset;}
    .ring-inner {width:76px; height:76px; border-radius:50%;
        background:rgba(255,255,255,.12); backdrop-filter:blur(4px);
        display:flex; flex-direction:column;
        align-items:center; justify-content:center; line-height:1;}
    .ring-num {font-size:1.8rem; font-weight:900;}
    .ring-cap {font-size:0.68rem; opacity:.85; margin-top:2px;}
    .hero-msg {flex:1; font-size:1.0rem; font-weight:700; line-height:1.5;
        text-shadow:0 1px 8px rgba(0,0,0,.15);}

    /* 節目バッジ */
    .badges {display:flex; gap:6px; margin-top:14px; flex-wrap:wrap;}
    .badge {flex:1; min-width:52px; text-align:center; border-radius:14px; padding:7px 2px;
        font-size:0.72rem; font-weight:800; background:rgba(255,255,255,.15); color:#eed;}
    .badge.on {background:rgba(255,255,255,.92); color:#ad5389; transform:scale(1.05);
        box-shadow:0 4px 12px rgba(0,0,0,.15);}
    .badge .b-ico {font-size:1.3rem; display:block;}

    /* サブカウンター */
    .subcount {background:#fff; border-radius:16px; padding:11px 14px; margin:6px 0 4px;
        font-weight:800; color:#7b1fa2; box-shadow:0 4px 12px rgba(0,0,0,.05);
        border-left:6px solid #ce93d8;}

    /* 難易度ピル */
    .pill {display:inline-block; padding:3px 14px; border-radius:999px; font-size:0.8rem;
        font-weight:800; color:#fff;}
    .pill.lv1 {background:#81c784;} .pill.lv2 {background:#ffb74d;} .pill.lv3 {background:#e57373;}

    /* 天気ボックス */
    .wx-row {display:flex; justify-content:space-between; gap:8px; margin-top:8px;}
    .wx-box {flex:1; text-align:center; border-radius:16px; padding:10px 4px;
        background:linear-gradient(160deg,#fce4ec,#f3e5f5);
        box-shadow:0 3px 10px rgba(0,0,0,.04);}
    .wx-day {font-size:0.78rem; color:#8e6280; font-weight:700;}
    .wx-ico {font-size:1.7rem; line-height:1.4;}
    .wx-tmp {font-size:0.85rem; color:#5d4037; font-weight:700;}
    .wx-idx {font-size:0.82rem; font-weight:800;}

    /* expander カード風 */
    .streamlit-expanderHeader, [data-testid="stExpander"] summary {
        font-weight:800 !important; font-size:1.02rem;}
    [data-testid="stExpander"] {border:none !important; border-radius:18px;
        background:#fff; box-shadow:0 4px 16px rgba(173,83,137,.08); margin-bottom:8px;
        border-left:4px solid #f48fb1 !important;}

    /* 進捗バー */
    .stProgress > div > div > div > div {
        background:linear-gradient(90deg,#f48fb1,#ce93d8,#9fa8da);}

    /* ===== ダークモード対策：テキストを必ず濃い色に ===== */
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] span,
    [data-testid="stAppViewContainer"] label,
    [data-testid="stAppViewContainer"] li,
    [data-testid="stAppViewContainer"] div {color: #4a3040;}
    /* ヒーロー内は白に戻す */
    .hero, .hero h1, .hero div, .hero span, .hero p {color: #fff !important;}
    .badge.on, .badge.on span {color: #ad5389 !important;}
    .subcount, .subcount span {color: #7b1fa2 !important;}
    .pill {color: #fff !important;}
    /* ボタン文字は白 */
    .stButton > button, .stFormSubmitButton > button {color: #fff !important;}

    /* ===== Streamlit ロゴ・ブランドボタンを完全非表示 ===== */
    footer, #MainMenu,
    header, header[data-testid="stHeader"],
    [data-testid="manage-app-button"],
    [data-testid="stStatusWidget"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stAppDeployButton"],
    .stDeployButton,
    .stAppDeployButton,
    div[class*="viewerBadge"],
    div[class*="StatusWidget"],
    div[class*="deploy" i],
    iframe[title*="badge"],
    a[href*="streamlit.io/cloud"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
        position: absolute !important;
        pointer-events: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# 日本百名山データ（全100座）
# (山名, 地域, 都道府県, 標高m, 緯度, 経度, 難易度)
# ※座標は概算です。実際の登山口は別途ご確認ください。
# ============================================================
RAW = [
    # --- 北海道 ---
    ("利尻岳", "北海道", "北海道", 1721, 45.178, 141.243, "上級"),
    ("羅臼岳", "北海道", "北海道", 1661, 44.073, 145.122, "中級"),
    ("斜里岳", "北海道", "北海道", 1547, 43.766, 144.717, "中級"),
    ("雌阿寒岳", "北海道", "北海道", 1499, 43.387, 144.008, "初級"),
    ("大雪山(旭岳)", "北海道", "北海道", 2291, 43.663, 142.854, "中級"),
    ("トムラウシ山", "北海道", "北海道", 2141, 43.527, 142.851, "上級"),
    ("十勝岳", "北海道", "北海道", 2077, 43.418, 142.686, "中級"),
    ("幌尻岳", "北海道", "北海道", 2053, 42.708, 142.689, "上級"),
    ("羊蹄山", "北海道", "北海道", 1898, 42.827, 140.811, "中級"),
    # --- 東北 ---
    ("岩木山", "東北", "青森県", 1625, 40.656, 140.303, "初級"),
    ("八甲田山", "東北", "青森県", 1585, 40.659, 140.877, "初級"),
    ("八幡平", "東北", "岩手県", 1613, 39.958, 140.854, "初級"),
    ("岩手山", "東北", "岩手県", 2038, 39.853, 141.001, "中級"),
    ("早池峰山", "東北", "岩手県", 1917, 39.557, 141.490, "中級"),
    ("鳥海山", "東北", "山形県", 2236, 39.099, 140.049, "中級"),
    ("月山", "東北", "山形県", 1984, 38.549, 140.027, "初級"),
    ("朝日岳", "東北", "山形県", 1871, 38.945, 139.918, "上級"),
    ("蔵王山", "東北", "山形県", 1841, 38.144, 140.440, "初級"),
    ("飯豊山", "東北", "福島県", 2105, 37.854, 139.708, "上級"),
    ("吾妻山", "東北", "福島県", 2035, 37.733, 140.246, "初級"),
    ("安達太良山", "東北", "福島県", 1700, 37.622, 140.288, "初級"),
    ("磐梯山", "東北", "福島県", 1816, 37.601, 140.073, "中級"),
    ("会津駒ヶ岳", "東北", "福島県", 2133, 37.046, 139.348, "中級"),
    # --- 関東 ---
    ("那須岳", "関東", "栃木県", 1915, 37.122, 139.963, "初級"),
    ("男体山", "関東", "栃木県", 2486, 36.766, 139.491, "中級"),
    ("日光白根山", "関東", "群馬県", 2578, 36.798, 139.377, "中級"),
    ("皇海山", "関東", "群馬県", 2144, 36.700, 139.337, "中級"),
    ("武尊山", "関東", "群馬県", 2158, 36.802, 139.137, "中級"),
    ("赤城山", "関東", "群馬県", 1828, 36.560, 139.193, "初級"),
    ("草津白根山", "関東", "群馬県", 2160, 36.643, 138.528, "初級"),
    ("谷川岳", "関東", "群馬県", 1977, 36.835, 138.929, "中級"),
    ("至仏山", "関東", "群馬県", 2228, 36.903, 139.173, "中級"),
    ("燧ヶ岳", "関東", "福島県", 2356, 36.955, 139.286, "中級"),
    ("平ヶ岳", "関東", "群馬県", 2141, 36.943, 139.178, "上級"),
    ("両神山", "関東", "埼玉県", 1723, 35.999, 138.838, "中級"),
    ("雲取山", "関東", "東京都", 2017, 35.857, 138.943, "中級"),
    ("丹沢山", "関東", "神奈川県", 1673, 35.474, 139.166, "中級"),
    ("筑波山", "関東", "茨城県", 877, 36.225, 140.107, "初級"),
    # --- 中部（北アルプス・八ヶ岳・中央/南アルプスなど） ---
    ("巻機山", "中部", "新潟県", 1967, 36.911, 138.985, "中級"),
    ("越後駒ヶ岳", "中部", "新潟県", 2003, 37.139, 139.137, "中級"),
    ("苗場山", "中部", "新潟県", 2145, 36.847, 138.694, "中級"),
    ("雨飾山", "中部", "新潟県", 1963, 36.910, 137.951, "中級"),
    ("妙高山", "中部", "新潟県", 2454, 36.892, 138.114, "中級"),
    ("火打山", "中部", "新潟県", 2462, 36.921, 138.061, "中級"),
    ("高妻山", "中部", "長野県", 2353, 36.789, 138.064, "上級"),
    ("四阿山", "中部", "長野県", 2354, 36.541, 138.408, "中級"),
    ("浅間山", "中部", "長野県", 2568, 36.406, 138.523, "中級"),
    ("白馬岳", "中部", "長野県", 2932, 36.758, 137.759, "上級"),
    ("五竜岳", "中部", "富山県", 2814, 36.665, 137.752, "上級"),
    ("鹿島槍ヶ岳", "中部", "富山県", 2889, 36.624, 137.747, "上級"),
    ("剱岳", "中部", "富山県", 2999, 36.623, 137.617, "上級"),
    ("立山", "中部", "富山県", 3015, 36.575, 137.618, "中級"),
    ("薬師岳", "中部", "富山県", 2926, 36.466, 137.546, "上級"),
    ("黒部五郎岳", "中部", "富山県", 2840, 36.397, 137.541, "上級"),
    ("水晶岳", "中部", "富山県", 2986, 36.428, 137.594, "上級"),
    ("鷲羽岳", "中部", "富山県", 2924, 36.408, 137.604, "上級"),
    ("槍ヶ岳", "中部", "長野県", 3180, 36.342, 137.648, "上級"),
    ("穂高岳", "中部", "長野県", 3190, 36.289, 137.648, "上級"),
    ("常念岳", "中部", "長野県", 2857, 36.324, 137.728, "中級"),
    ("笠ヶ岳", "中部", "岐阜県", 2898, 36.313, 137.582, "上級"),
    ("焼岳", "中部", "長野県", 2455, 36.227, 137.587, "中級"),
    ("乗鞍岳", "中部", "長野県", 3026, 36.106, 137.553, "初級"),
    ("御嶽山", "中部", "長野県", 3067, 35.893, 137.480, "中級"),
    ("美ヶ原", "中部", "長野県", 2034, 36.224, 138.110, "初級"),
    ("霧ヶ峰", "中部", "長野県", 1925, 36.103, 138.193, "初級"),
    ("蓼科山", "中部", "長野県", 2531, 36.103, 138.296, "初級"),
    ("八ヶ岳(赤岳)", "中部", "長野県", 2899, 35.971, 138.370, "中級"),
    ("甲武信ヶ岳", "中部", "山梨県", 2475, 35.910, 138.731, "中級"),
    ("金峰山", "中部", "山梨県", 2599, 35.871, 138.625, "中級"),
    ("瑞牆山", "中部", "山梨県", 2230, 35.893, 138.583, "中級"),
    ("大菩薩嶺", "中部", "山梨県", 2057, 35.748, 138.745, "初級"),
    ("富士山", "中部", "山梨県", 3776, 35.360, 138.727, "中級"),
    ("天城山", "中部", "静岡県", 1406, 34.857, 139.000, "初級"),
    ("木曽駒ヶ岳", "中部", "長野県", 2956, 35.789, 137.804, "中級"),
    ("空木岳", "中部", "長野県", 2864, 35.703, 137.819, "上級"),
    ("恵那山", "中部", "長野県", 2191, 35.439, 137.595, "中級"),
    ("甲斐駒ヶ岳", "中部", "山梨県", 2967, 35.758, 138.237, "上級"),
    ("仙丈ヶ岳", "中部", "山梨県", 3033, 35.720, 138.183, "中級"),
    ("鳳凰山", "中部", "山梨県", 2841, 35.696, 138.296, "中級"),
    ("北岳", "中部", "山梨県", 3193, 35.674, 138.239, "上級"),
    ("間ノ岳", "中部", "山梨県", 3190, 35.646, 138.227, "上級"),
    ("塩見岳", "中部", "長野県", 3052, 35.568, 138.179, "上級"),
    ("荒川岳(悪沢岳)", "中部", "静岡県", 3141, 35.470, 138.179, "上級"),
    ("赤石岳", "中部", "長野県", 3121, 35.460, 138.158, "上級"),
    ("聖岳", "中部", "長野県", 3013, 35.420, 138.143, "上級"),
    ("光岳", "中部", "長野県", 2592, 35.336, 138.085, "上級"),
    ("白山", "中部", "石川県", 2702, 36.155, 136.771, "中級"),
    ("荒島岳", "中部", "福井県", 1523, 35.927, 136.595, "中級"),
    # --- 近畿 ---
    ("伊吹山", "近畿", "滋賀県", 1377, 35.418, 136.406, "初級"),
    ("大台ヶ原山", "近畿", "奈良県", 1695, 34.183, 136.108, "初級"),
    ("大峰山(八経ヶ岳)", "近畿", "奈良県", 1915, 34.171, 135.910, "中級"),
    # --- 中国・四国 ---
    ("大山", "中国", "鳥取県", 1729, 35.371, 133.546, "中級"),
    ("剣山", "四国", "徳島県", 1955, 33.854, 134.094, "初級"),
    ("石鎚山", "四国", "愛媛県", 1982, 33.768, 133.115, "中級"),
    # --- 九州 ---
    ("九重山", "九州", "大分県", 1791, 33.087, 131.249, "中級"),
    ("祖母山", "九州", "大分県", 1756, 32.825, 131.346, "中級"),
    ("阿蘇山", "九州", "熊本県", 1592, 32.884, 131.104, "初級"),
    ("霧島山(韓国岳)", "九州", "宮崎県", 1700, 31.934, 130.861, "初級"),
    ("開聞岳", "九州", "鹿児島県", 924, 31.180, 130.528, "初級"),
    ("宮之浦岳", "九州", "鹿児島県", 1936, 30.337, 130.508, "上級"),
]

MOUNTAINS = [
    {"id": i, "name": n, "region": reg, "pref": pref,
     "elev": e, "lat": la, "lon": lo, "level": lv}
    for i, (n, reg, pref, e, la, lo, lv) in enumerate(RAW)
]

REGION_ORDER = ["北海道", "東北", "関東", "中部", "近畿", "中国", "四国", "九州"]

# 「現在地から探す」の拠点候補（主要都市の概算座標）
BASE_POINTS = {
    "札幌": (43.06, 141.35), "仙台": (38.27, 140.87), "東京": (35.69, 139.69),
    "横浜": (35.44, 139.64), "さいたま": (35.86, 139.65), "宇都宮": (36.57, 139.88),
    "前橋": (36.39, 139.06), "新潟": (37.90, 139.02), "長野": (36.65, 138.18),
    "松本": (36.24, 137.97), "甲府": (35.66, 138.57), "名古屋": (35.18, 136.91),
    "金沢": (36.59, 136.63), "大阪": (34.69, 135.50), "広島": (34.39, 132.46),
    "高松": (34.34, 134.05), "福岡": (33.59, 130.40), "鹿児島": (31.60, 130.56),
}

# ============================================================
# 記録の読み書き（CSV保存 → 再起動しても消えない）
# ============================================================
def load_records():
    """records.csv を読み込んで dict[id] = {date, memo, photo} を返す"""
    recs = {}
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    recs[int(row["id"])] = {
                        "date": row.get("date", ""),
                        "memo": row.get("memo", ""),
                        "photo": row.get("photo", ""),
                    }
                except (ValueError, KeyError):
                    continue
    return recs


def save_records(recs):
    """dict をまるごと CSV に書き出す（last-write-wins）"""
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "date", "memo", "photo"])
        w.writeheader()
        for mid, r in recs.items():
            w.writerow({"id": mid, "date": r["date"], "memo": r["memo"], "photo": r["photo"]})


CUSTOM_CSV = os.path.join(DATA_DIR, "custom_mountains.csv")


def load_custom():
    """百名山以外に自分で登録した山を読み込む"""
    out = []
    if os.path.exists(CUSTOM_CSV):
        with open(CUSTOM_CSV, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    out.append({
                        "cid": int(row["cid"]), "name": row["name"],
                        "lat": float(row["lat"]), "lon": float(row["lon"]),
                        "level": row.get("level", "中級"), "date": row.get("date", ""),
                        "memo": row.get("memo", ""), "photo": row.get("photo", ""),
                    })
                except (ValueError, KeyError):
                    continue
    return out


def save_custom(lst):
    with open(CUSTOM_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["cid", "name", "lat", "lon",
                                          "level", "date", "memo", "photo"])
        w.writeheader()
        for r in lst:
            w.writerow(r)


def add_custom_mountain(name, d, level, memo, uploaded):
    cid = (max(c["cid"] for c in st.session_state.custom) + 1) if st.session_state.custom else 1
    photo = ""
    if uploaded is not None:
        ext = os.path.splitext(uploaded.name)[1].lower() or ".jpg"
        photo = os.path.join(PHOTO_DIR, f"c{cid:03d}{ext}")
        with open(photo, "wb") as f:
            f.write(uploaded.getbuffer())
    st.session_state.custom.append({
        "cid": cid, "name": name.strip(),
        "lat": round(st.session_state.new_lat, 5),
        "lon": round(st.session_state.new_lon, 5),
        "level": level, "date": d.isoformat(),
        "memo": memo or "", "photo": photo,
    })
    save_custom(st.session_state.custom)


if "records" not in st.session_state:
    st.session_state.records = load_records()
if "custom" not in st.session_state:
    st.session_state.custom = load_custom()

# 計画モードのステップ管理
st.session_state.setdefault("sel_region", None)
st.session_state.setdefault("sel_pref", None)
st.session_state.setdefault("new_lat", None)
st.session_state.setdefault("new_lon", None)


# ============================================================
# 天気（最初はモック / 将来 Open-Meteo に差し替え可能）
# ============================================================
DAY_LABELS = ["明日", "明後日", "明々後日"]
WX_PRESET = {
    "sun":   {"ico": "☀️", "idx": "A", "color": "#1b7f2e"},
    "cloud": {"ico": "⛅",  "idx": "B", "color": "#b58900"},
    "rain":  {"ico": "🌧️", "idx": "C", "color": "#c0392b"},
}


def mock_weather(mtn):
    """山ごとに安定したダミー天気を生成（標高・座標から擬似乱数）"""
    seed = (mtn["id"] * 7 + int(mtn["elev"])) % 9
    patterns = [
        ["sun", "sun", "cloud"], ["cloud", "sun", "sun"], ["sun", "cloud", "rain"],
        ["cloud", "cloud", "sun"], ["rain", "cloud", "sun"], ["sun", "sun", "sun"],
        ["cloud", "rain", "cloud"], ["sun", "cloud", "cloud"], ["rain", "sun", "cloud"],
    ]
    pat = patterns[seed]
    base = max(2, 22 - mtn["elev"] // 200)  # 標高が高いほど寒い
    out = []
    for i, code in enumerate(pat):
        p = WX_PRESET[code]
        tmax = base + (2 - i)
        out.append({"label": DAY_LABELS[i], "ico": p["ico"], "idx": p["idx"],
                    "color": p["color"], "tmax": tmax, "tmin": tmax - 7})
    return out


def real_weather(mtn):
    """Open-Meteo から本物の3日間予報を取得（APIキー不要・要ネット）。失敗時はモック。"""
    try:
        import requests
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": mtn["lat"], "longitude": mtn["lon"],
            "daily": "weathercode,temperature_2m_max,temperature_2m_min",
            "timezone": "Asia/Tokyo", "forecast_days": 4,
        }
        d = requests.get(url, params=params, timeout=6).json()["daily"]
        out = []
        for i in range(1, 4):  # 当日(0)はスキップし、明日以降3日分
            code = d["weathercode"][i]
            if code <= 1:
                cat = "sun"
            elif code <= 48:
                cat = "cloud"
            else:
                cat = "rain"
            p = WX_PRESET[cat]
            out.append({"label": DAY_LABELS[i - 1], "ico": p["ico"], "idx": p["idx"],
                        "color": p["color"],
                        "tmax": round(d["temperature_2m_max"][i]),
                        "tmin": round(d["temperature_2m_min"][i])})
        return out
    except Exception:
        return mock_weather(mtn)


def get_weather(mtn):
    if st.session_state.get("use_real_weather"):
        return real_weather(mtn)
    return mock_weather(mtn)


def weather_html(forecast):
    boxes = ""
    for d in forecast:
        boxes += (
            f"<div class='wx-box'>"
            f"<div class='wx-day'>{d['label']}</div>"
            f"<div class='wx-ico'>{d['ico']}</div>"
            f"<div class='wx-tmp'>{d['tmax']}° / {d['tmin']}°</div>"
            f"<div class='wx-idx' style='color:{d['color']}'>指数 {d['idx']}</div>"
            f"</div>"
        )
    return f"<div class='wx-row'>{boxes}</div>"


# ============================================================
# 距離計算（ハバーサイン）
# ============================================================
def distance_km(lat1, lon1, lat2, lon2):
    R = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ============================================================
# 記録の保存処理（写真をディスクに保存 → CSV更新）
# ============================================================
def register_climb(mtn, climb_date, memo, uploaded):
    photo_path = ""
    existing = st.session_state.records.get(mtn["id"], {})
    if uploaded is not None:
        ext = os.path.splitext(uploaded.name)[1].lower() or ".jpg"
        photo_path = os.path.join(PHOTO_DIR, f"m{mtn['id']:03d}{ext}")
        with open(photo_path, "wb") as f:
            f.write(uploaded.getbuffer())
    elif existing.get("photo"):
        photo_path = existing["photo"]  # 写真未選択なら既存を維持

    st.session_state.records[mtn["id"]] = {
        "date": climb_date.isoformat(),
        "memo": memo or "",
        "photo": photo_path,
    }
    save_records(st.session_state.records)


# ============================================================
# 1座ぶんのカード描画（計画タブ等で共通利用）
# ============================================================
def render_mountain_card(mtn, key_prefix):
    rec = st.session_state.records.get(mtn["id"])
    done = "✅ " if rec else ""
    title = f"{done}{mtn['name']}　{mtn['elev']}m　{LEVEL_EMOJI[mtn['level']]}"
    with st.expander(title, expanded=False):
        st.markdown(weather_html(get_weather(mtn)), unsafe_allow_html=True)
        lvcls = {"初級": "lv1", "中級": "lv2", "上級": "lv3"}[mtn["level"]]
        st.markdown(
            f"<div style='margin-top:8px;'>📍 {mtn['pref']}（{mtn['region']}）　"
            f"<span class='pill {lvcls}'>{mtn['level']}</span></div>",
            unsafe_allow_html=True,
        )

        if rec:
            st.success(f"登頂済み：{rec['date']}")
            if rec.get("memo"):
                st.write("📝 " + rec["memo"])
            if rec.get("photo") and os.path.exists(rec["photo"]):
                st.image(rec["photo"], use_container_width=True)

        # 登頂記録フォーム
        with st.form(key=f"{key_prefix}_form_{mtn['id']}"):
            st.markdown("**🏁 登頂を記録する**")
            d = st.date_input("登った日", value=date.today(),
                              key=f"{key_prefix}_date_{mtn['id']}")
            memo = st.text_input("一言メモ", value=(rec or {}).get("memo", ""),
                                 key=f"{key_prefix}_memo_{mtn['id']}")
            photo = st.file_uploader("写真（カメラ / 写真フォルダ）",
                                     type=["jpg", "jpeg", "png"],
                                     key=f"{key_prefix}_photo_{mtn['id']}")
            if st.form_submit_button("💾 登った！として保存"):
                register_climb(mtn, d, memo, photo)
                st.balloons()
                st.success("🎉 登頂おめでとう！フォトマップに反映されます。")
                st.rerun()


# ============================================================
# ヘッダー（達成度ヒーローバナー）
# ============================================================
done_count = len(st.session_state.records)
pct = done_count / 100
deg = int(pct * 360)


def cheer_message(n):
    if n >= 100:
        return "🌸 百名山ぜんぶ登頂！あなたは最高です！✨"
    if n >= 90:
        return "💎 あと少し…！ゴールがすぐそこに見えてる！"
    if n >= 70:
        return "🌈 70座超え！ここからの景色、最高だね！"
    if n >= 50:
        return "🎀 折り返し達成！すごいすごい！"
    if n >= 30:
        return "🌷 30座突破！どんどん世界が広がるね"
    if n >= 10:
        return "☀️ 順調！次はどの山に会いに行こう？"
    if n >= 1:
        return "🌿 はじめの一歩、おめでとう！"
    return "🥾 さあ、最初の一座に会いに行こう♪"


MILESTONES = [(10, "🌿"), (30, "🌷"), (50, "🎀"), (70, "🌈"), (100, "👑")]
badge_html = ""
for need, ico in MILESTONES:
    on = "on" if done_count >= need else ""
    badge_html += (f"<div class='badge {on}'><span class='b-ico'>{ico}</span>"
                   f"{need}座</div>")

st.markdown(
    f"""
    <div class="hero">
      <h1>🌸 わたしの百名山</h1>
      <div class="sub">登山ログ・天気・フォトマップ</div>
      <div class="hero-row">
        <div class="ring" style="background:conic-gradient(#f8bbd0 {deg}deg, rgba(255,255,255,.18) 0);">
          <div class="ring-inner">
            <div class="ring-num">{done_count}</div>
            <div class="ring-cap">/ 100座</div>
          </div>
        </div>
        <div class="hero-msg">{cheer_message(done_count)}</div>
      </div>
      <div class="badges">{badge_html}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.custom:
    st.markdown(
        f"<div class='subcount'>🗻 百名山以外にも "
        f"<span style='color:#7b1fa2;'>{len(st.session_state.custom)} 座</span> 登頂済み！</div>",
        unsafe_allow_html=True,
    )

st.session_state.use_real_weather = st.toggle(
    "🌐 リアルタイム天気を使う（要ネット接続）", value=USE_REAL_WEATHER_DEFAULT,
    help="ONにすると Open-Meteo から本物の3日間予報を取得します。",
)

# ============================================================
# メインナビ（タブ）
# ============================================================
tab_plan, tab_map, tab_add, tab_auto = st.tabs(
    ["🗺️ 計画", "📸 マップ", "➕ 山を追加", "📍 おまかせ"])

# ------------------------------------------------------------
# タブ1：計画する（地域 → 都道府県 → 山リスト）
# ------------------------------------------------------------
with tab_plan:
    # ステップ1：地域選択
    if st.session_state.sel_region is None:
        st.subheader("① 地域を選ぶ")
        region_icon = {"北海道": "❄️", "東北": "🌸", "関東": "🗼", "中部": "🏔️",
                       "近畿": "🦌", "中国": "🍁", "四国": "🌊", "九州": "🌺"}
        ids_by_region = {r: [m["id"] for m in MOUNTAINS if m["region"] == r]
                         for r in REGION_ORDER}
        for reg in REGION_ORDER:
            ids = ids_by_region[reg]
            n = len(ids)
            d = sum(1 for i in ids if i in st.session_state.records)
            ico = region_icon.get(reg, "⛰️")
            if st.button(f"{ico} {reg}　{d}/{n}座", key=f"reg_{reg}"):
                st.session_state.sel_region = reg
                st.session_state.sel_pref = None
                st.rerun()

    # ステップ2：都道府県選択
    elif st.session_state.sel_pref is None:
        if st.button("← 地域選択にもどる"):
            st.session_state.sel_region = None
            st.rerun()
        st.subheader(f"② 都道府県を選ぶ（{st.session_state.sel_region}）")
        prefs = sorted({m["pref"] for m in MOUNTAINS
                        if m["region"] == st.session_state.sel_region})
        if st.button("◎ この地域すべて表示", key="all_pref"):
            st.session_state.sel_pref = "__ALL__"
            st.rerun()
        for p in prefs:
            n = sum(1 for m in MOUNTAINS
                    if m["region"] == st.session_state.sel_region and m["pref"] == p)
            if st.button(f"{p}　（{n}座）", key=f"pref_{p}"):
                st.session_state.sel_pref = p
                st.rerun()

    # ステップ3：山リスト
    else:
        if st.button("← 都道府県選択にもどる"):
            st.session_state.sel_pref = None
            st.rerun()
        reg = st.session_state.sel_region
        pref = st.session_state.sel_pref
        if pref == "__ALL__":
            st.subheader(f"③ {reg} の百名山")
            mts = [m for m in MOUNTAINS if m["region"] == reg]
        else:
            st.subheader(f"③ {pref} の百名山")
            mts = [m for m in MOUNTAINS if m["region"] == reg and m["pref"] == pref]
        st.caption("各山をタップ → 3日間の天気と登頂記録フォームが開きます")
        for m in mts:
            render_mountain_card(m, key_prefix="plan")

# ------------------------------------------------------------
# タブ2：記録＆フォトマップ
# ------------------------------------------------------------
with tab_map:
    st.subheader("📸 登頂フォトマップ")
    st.caption("🟢 登った百名山 / ⚪ まだの百名山 / 🔵 百名山以外。ピンをタップで写真が出ます。")

    fmap = folium.Map(location=[37.5, 138.0], zoom_start=5, control_scale=True)
    for m in MOUNTAINS:
        rec = st.session_state.records.get(m["id"])
        if rec:
            # 登頂済み：緑ピン＋写真ポップアップ
            img_html = ""
            if rec.get("photo") and os.path.exists(rec["photo"]):
                with open(rec["photo"], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                img_html = (f"<img src='data:image/jpeg;base64,{b64}' "
                            f"style='width:200px;border-radius:8px;margin-top:4px;'>")
            popup = (f"<b>{html.escape(m['name'])}</b> ({m['elev']}m)<br>"
                     f"📅 {html.escape(rec['date'])}<br>"
                     f"📝 {html.escape(rec.get('memo',''))}<br>{img_html}")
            folium.Marker([m["lat"], m["lon"]], tooltip=m["name"],
                          popup=folium.Popup(popup, max_width=240),
                          icon=folium.Icon(color="green", icon="flag")).add_to(fmap)
        else:
            popup = f"<b>{html.escape(m['name'])}</b> ({m['elev']}m)<br>{m['pref']}<br>未登頂"
            folium.Marker([m["lat"], m["lon"]], tooltip=m["name"],
                          popup=folium.Popup(popup, max_width=200),
                          icon=folium.Icon(color="lightgray", icon="cloud")).add_to(fmap)

    # 百名山以外（自分で登録した山）：青ピン
    for c in st.session_state.custom:
        img_html = ""
        if c.get("photo") and os.path.exists(c["photo"]):
            with open(c["photo"], "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            img_html = (f"<img src='data:image/jpeg;base64,{b64}' "
                        f"style='width:200px;border-radius:8px;margin-top:4px;'>")
        popup = (f"<b>{html.escape(c['name'])}</b><br>"
                 f"📅 {html.escape(c['date'])}<br>"
                 f"📝 {html.escape(c.get('memo',''))}<br>{img_html}")
        folium.Marker([c["lat"], c["lon"]], tooltip=c["name"],
                      popup=folium.Popup(popup, max_width=240),
                      icon=folium.Icon(color="blue", icon="star")).add_to(fmap)

    st_folium(fmap, height=440, use_container_width=True, returned_objects=[])

    # 登頂済み一覧
    if st.session_state.records:
        st.markdown("### ✅ 登頂済みリスト")
        id2m = {m["id"]: m for m in MOUNTAINS}
        for mid, r in sorted(st.session_state.records.items(),
                             key=lambda x: x[1]["date"], reverse=True):
            m = id2m.get(mid)
            if m:
                st.write(f"・**{m['name']}**（{r['date']}） {r.get('memo','')}")

# ------------------------------------------------------------
# タブ3：百名山以外の山を追加（地図タップで場所指定）
# ------------------------------------------------------------
with tab_add:
    st.subheader("➕ 百名山以外の山を記録")
    st.caption("地図をタップ → 場所を選び、山名・写真を保存できます。どんな山でもOK。")

    amap = folium.Map(location=[37.5, 138.0], zoom_start=5, control_scale=True)
    for c in st.session_state.custom:
        folium.Marker([c["lat"], c["lon"]], tooltip=c["name"],
                      icon=folium.Icon(color="blue", icon="star")).add_to(amap)
    clicked = st_folium(amap, height=360, use_container_width=True,
                        returned_objects=["last_clicked"])
    if clicked and clicked.get("last_clicked"):
        st.session_state.new_lat = clicked["last_clicked"]["lat"]
        st.session_state.new_lon = clicked["last_clicked"]["lng"]

    if st.session_state.new_lat is not None:
        st.info(f"📍 選択地点：緯度 {st.session_state.new_lat:.4f} / "
                f"経度 {st.session_state.new_lon:.4f}")
    else:
        st.warning("まず地図をタップして、山の場所を選んでください。")

    with st.form("add_custom_form"):
        name = st.text_input("山名（必須）", placeholder="例：高尾山")
        d = st.date_input("登った日", value=date.today())
        level = st.selectbox("難易度", ["初級", "中級", "上級"], index=1)
        memo = st.text_input("一言メモ")
        photo = st.file_uploader("写真（カメラ / 写真フォルダ）",
                                 type=["jpg", "jpeg", "png"])
        if st.form_submit_button("💾 この山を保存"):
            if not name.strip():
                st.error("山名を入れてください。")
            elif st.session_state.new_lat is None:
                st.error("地図で場所を選んでください。")
            else:
                add_custom_mountain(name, d, level, memo, photo)
                st.session_state.new_lat = None
                st.session_state.new_lon = None
                st.balloons()
                st.success("🎉 登頂おめでとう！マップタブに青ピンで表示されます。")
                st.rerun()

    if st.session_state.custom:
        st.markdown("### 🗻 記録した山（百名山以外）")
        for c in sorted(st.session_state.custom, key=lambda x: x["date"], reverse=True):
            col1, col2 = st.columns([4, 1])
            col1.write(f"**{c['name']}**（{c['date']}） {c.get('memo','')}")
            if col2.button("削除", key=f"del_custom_{c['cid']}"):
                st.session_state.custom = [
                    x for x in st.session_state.custom if x["cid"] != c["cid"]]
                save_custom(st.session_state.custom)
                st.rerun()

# ------------------------------------------------------------
# タブ4：おまかせ即時検索（現在地から近い・天気の良い山）
# ------------------------------------------------------------
with tab_auto:
    st.subheader("📍 今週末どこ行く？ おまかせ検索")

    base_name = st.selectbox("拠点（現在地に近い場所）を選ぶ",
                             list(BASE_POINTS.keys()), index=2)  # 既定:東京
    blat, blon = BASE_POINTS[base_name]
    st.caption("※スマホのGPSで本当の現在地を使いたい場合は、最後の解説で streamlit-geolocation の導入方法を参照。")

    levels = st.multiselect("難易度でしぼる", ["初級", "中級", "上級"],
                            default=["初級", "中級"])
    only_good = st.toggle("☀️ 直近3日に「指数A（好天）」がある山だけ", value=True)
    topn = st.slider("表示する数", 3, 15, 5)

    if st.button("🔎 おすすめの山を探す"):
        cands = []
        for m in MOUNTAINS:
            if m["level"] not in levels:
                continue
            fc = get_weather(m)
            has_good = any(d["idx"] == "A" for d in fc)
            if only_good and not has_good:
                continue
            dist = distance_km(blat, blon, m["lat"], m["lon"])
            cands.append((dist, m, fc))
        cands.sort(key=lambda x: x[0])

        if not cands:
            st.warning("条件に合う山が見つかりませんでした。条件をゆるめてみてください。")
        else:
            st.success(f"{base_name} から近い順におすすめ {min(topn, len(cands))} 座")
            for dist, m, fc in cands[:topn]:
                done = "✅ " if m["id"] in st.session_state.records else ""
                st.markdown(f"#### {done}{m['name']} "
                            f"<span style='font-size:0.8rem;color:#777'>"
                            f"約{dist:.0f}km / {m['elev']}m / {LEVEL_EMOJI[m['level']]}</span>",
                            unsafe_allow_html=True)
                st.markdown(weather_html(fc), unsafe_allow_html=True)
                st.divider()

st.caption("天気は現在ダミー表示です。上部トグルでOpen-Meteoの実データに切替できます。")
