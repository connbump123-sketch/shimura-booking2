import streamlit as st
import time
import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from PIL import Image
import os

# --- ページ設定 ---
st.set_page_config(
    page_title="しむら小児科予約",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- デザイン調整 (CSS) ---
st.markdown("""
    <style>
    /* ============================
       フォント設定（丸ゴシック化）
    ============================ */
    @import url('https://fonts.googleapis.com/css2?family=Kosugi+Maru&display=swap');
    
    html, body, [class*="css"], font, span, div, p, h1, h2, h3, h4, h5, h6, button, input, select, label {
        font-family: 'Kosugi Maru', "Hiragino Maru Gothic ProN", "HGMaruGothicMPRO", "Yu Gothic Medium", "Yu Gothic", sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }

    /* ============================
       レイアウト設定
    ============================ */
    /* ヘッダー被り対策 & 下部スペース確保 */
    .block-container {
        padding-top: 4.5rem !important; /* ロゴが隠れないよう大幅に増やす */
        padding-bottom: 20rem !important; 
        max-width: 100% !important;
    }

    /* ============================
       タイトル・キャプション周りの空白削除
    ============================ */
    /* タイトル */
    h1 {
        display: block !important;
        font-size: 1.1rem !important;
        text-align: center !important;
        color: #555555 !important;
        margin-top: 0.2rem !important; /* 上を少し詰める */
        margin-bottom: 0 !important;
        padding: 0 !important;
    }

    /* キャプションのテキスト自体 */
    div[data-testid="stCaptionContainer"] p {
        font-size: 0.8rem !important;
        color: #555555 !important;
        text-align: center;
        margin-top: 0 !important;
        margin-bottom: 0.2rem !important; /* 下の余白を極限まで減らす */
        line-height: 1.4 !important;
    }
    
    /* キャプションのコンテナを上に引き上げる */
    div[data-testid="stCaptionContainer"] {
        padding-top: 0 !important;
        margin-top: -0.8rem !important; /* 強力に上に詰める */
        margin-bottom: 0 !important;
    }

    /* ============================
       見出し・ラベルのデザイン & 空白削除
    ============================ */
    h3 {
        font-size: 1.1rem !important;
        font-weight: bold !important;
        margin-top: 0.8rem !important; /* 上は少し空ける */
        margin-bottom: 0.2rem !important; /* 下の余白を狭くする */
        color: #555555 !important;
    }
    
    /* カスタムラベル */
    .custom-label {
        font-size: 1.1rem;
        font-weight: bold;
        color: #555555;
        margin-bottom: 0.1rem; /* 下の余白を狭くする */
        font-family: 'Kosugi Maru', sans-serif;
    }

    /* ============================
       入力フォームのデザイン
    ============================ */
    /* ラジオボタン */
    div[role="radiogroup"] label:not(:has(input:checked)) p { color: #cccccc !important; }
    div[role="radiogroup"] label:not(:has(input:checked)) > div:first-child {
        border: 2px solid #e0e0e0 !important; background-color: #fafafa !important;
    }
    div[role="radiogroup"] label:has(input:checked) p { color: #4CAF50 !important; font-weight: bold !important; }
    div[role="radiogroup"] label:has(input:checked) > div:first-child {
        border-color: #4CAF50 !important; background-color: #4CAF50 !important;
    }
    div[role="radiogroup"] label:has(input:checked) > div:first-child svg { fill: #ffffff !important; }
    div[role="radiogroup"] p { font-size: 1rem !important; margin-bottom: 0 !important; } /* 余白削除 */

    /* ドロップダウンリスト */
    div[data-baseweb="select"] > div {
        background-color: #556b2f !important; border-color: #556b2f !important; color: #ffffff !important;
    }
    div[data-baseweb="select"] span { color: #ffffff !important; font-size: 1rem !important; }
    div[data-baseweb="select"] svg { fill: #ffffff !important; }
    
    /* ============================
       実行ボタン（空白削除・改行防止）
    ============================ */
    div.stButton > button {
        background-color: #f6adad !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100% !important;
        padding: 0.8em 0 !important;
        margin-top: 0.2rem !important; /* 上の余白を狭くする */
        font-size: 1.1rem !important;
        white-space: nowrap !important;
    }
    
    /* 背景設定 */
    .stApp { background-color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# --- ヘッダー（ロゴ表示） ---
logo_file = None
if os.path.exists("logo.png"): logo_file = "logo.png"
elif os.path.exists("logo.jpg"): logo_file = "logo.jpg"
elif os.path.exists("logo.jpeg"): logo_file = "logo.jpeg"

if logo_file:
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        st.image(logo_file, use_container_width=True)
else:
    st.error("⚠️ 画像が見つかりません。")

# タイトル
st.title("事前予約アプリ　〜大村家 専用〜")

# キャプション
st.caption("前日の夜にセットし、画面をつけたまま充電して寝てください。")

# --- 1. 予約設定 ---
st.subheader("1. 予約設定")

with st.container():
    # 子供選択
    target_child_str = st.radio(
        "予約するお子様",
        ["オオムラ イブキ 様 (12979)", "オオムラ エリナ 様 (10865)"],
        index=0,
        label_visibility="collapsed"
    )

    # 時間選択
    st.write("") # 最小限の隙間
    st.markdown('<div class="custom-label">2. 予約希望時間</div>', unsafe_allow_html=True)
    
    target_time_str = st.selectbox(
        "予約希望時間（ラベル非表示）",
        [f"{h:02d}:{m:02d}" for h in range(9, 18) for m in [0, 15, 30, 45] 
         if not (h == 12 and m > 0) and not (h > 12 and h < 15) and not (h == 17 and m > 30)],
        index=0,
        label_visibility="collapsed"
    )

# 設定値抽出
TARGET_ID = "12979" if "12979" in target_child_str else "10865"
TARGET_NAME = "イブキ" if "イブキ" in target_child_str else "エリナ"
TARGET_H = target_time_str.split(':')[0]
TARGET_M = target_time_str.split(':')[1]
TARGET_H_JP = f"{int(TARGET_H)}時"
TARGET_M_JP = f"{TARGET_H}時{TARGET_M}分"
START_URL = "https://shimura-kids.com/yoyaku/php/line_login.php"

# --- ブラウザ設定 ---
def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1')
    return webdriver.Chrome(options=options)

# --- 3. 予約実行 ---
st.subheader("3. 予約実行")

# 【重要】誤爆防止のため、ボタンの機能は現在コメントアウトされています
if st.button("🌙 おやすみ前セット（待機開始）"):
    st.toast("⚠️ 現在、誤作動防止のためコードは無効化されています。")
    st.info("デザイン確認モードです。本番使用時はコード内のコメントアウト（#）を解除してください。")
    
    """
    # --- 以下、本番用コード（現在は無効化中） ---
    
    # ログ表示エリア
    status_placeholder = st.empty()
    
    # 時間計算
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.datetime.now(jst)
    target_dt = now.replace(hour=6, minute=0, second=0, microsecond=0)
    if now.hour >= 6:
        target_dt += datetime.timedelta(days=1)
    
    # 先行ログイン開始時間（10分前）
    login_start_dt = target_dt - datetime.timedelta(minutes=10)
    
    # --- Phase 1: 待機 ---
    status_placeholder.markdown(f'''
        <div style="padding:1rem; border-radius:8px; background-color:#f1f8e9; border:1px solid #c8e6c9;">
            <h3 style="margin:0; font-size:1rem; color:#4CAF50 !important;">✅ セット完了</h3>
            <p style="margin:0; color:#555;"><b>{login_start_dt.strftime('%H:%M')}</b> に先行ログインします。</p>
        </div>
    ''', unsafe_allow_html=True)
    
    # 待機ループ
    while True:
        now = datetime.datetime.now(jst)
        wait_sec = (login_start_dt - now).total_seconds()
        if wait_sec <= 0: break
        if wait_sec > 60: time.sleep(10)
        else: time.sleep(1)

    driver = None
    try:
        # driver = get_driver()
        # ...
        pass
    except Exception as e:
        st.error(f"エラー: {e}")
    finally:
        if driver:
            driver.quit()
    """
