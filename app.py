import streamlit as st
import time
import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

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
    /* 1. ヘッダー被り対策：全体の開始位置を大きく下げる */
    .block-container {
        padding-top: 4rem !important; /* 余白を広げました */
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }
    
    /* 2. タイトルのサイズ調整 */
    h1 {
        font-size: 1.4rem !important;
        margin-bottom: 0.2rem !important;
        color: #333333 !important;
    }
    
    /* 3. ラジオボタンのデザイン (緑基調) */
    /* テキストの色（通常時は濃いグレー） */
    div[role="radiogroup"] p {
        color: #555555 !important;
        font-weight: bold !important;
    }
    
    /* 未選択の丸（グレー枠、中白） */
    div[role="radiogroup"] label > div:first-child {
        border: 2px solid #9e9e9e !important;
        background-color: #ffffff !important;
    }
    
    /* 選択された状態（ここを修正：緑背景、中白） */
    /* :hasセレクタを使用して、チェックされた状態を狙い撃ちします */
    div[role="radiogroup"] label:has(input:checked) > div:first-child {
        border-color: #4CAF50 !important; /* サイトの緑 */
        background-color: #4CAF50 !important;
    }
    /* 中の白い点（SVG） */
    div[role="radiogroup"] label:has(input:checked) > div:first-child svg {
        fill: #ffffff !important;
    }
    /* 選択された時のテキスト色 */
    div[role="radiogroup"] label:has(input:checked) p {
        color: #4CAF50 !important;
    }

    /* 4. ドロップダウンリスト（モスグリーン） */
    /* リストのコンテナ（ポップオーバー） */
    div[data-baseweb="popover"] div[role="listbox"],
    div[data-baseweb="popover"] ul {
        background-color: #556b2f !important; /* モスグリーン */
    }
    /* リスト内の文字色（白） */
    div[data-baseweb="popover"] li, 
    div[data-baseweb="popover"] div {
        color: #ffffff !important;
    }
    /* 選択中の項目のハイライト */
    div[data-baseweb="popover"] li[aria-selected="true"],
    div[data-baseweb="popover"] li:hover {
        background-color: #3b4a1c !important; /* さらに濃いモスグリーン */
        color: #ffffff !important;
    }
    
    /* 入力ボックス自体の色修正 */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border-color: #cccccc !important;
        color: #333333 !important;
    }
    /* 選択後の表示文字色 */
    div[data-baseweb="select"] span {
        color: #333333 !important;
    }

    /* 5. 実行ボタン（ピンク） */
    div.stButton > button {
        background-color: #f6adad !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100% !important;
        padding: 0.5em 1em !important;
        margin-top: 0.5rem !important;
    }

    /* 6. 背景白・文字グレー強制 */
    .stApp {
        background-color: #ffffff !important;
        color: #333333 !important;
    }
    
    /* ステータスボックス */
    .status-box {
        padding: 1rem;
        border-radius: 8px;
        background-color: #f1f8e9; /* 薄い緑背景 */
        border: 1px solid #c8e6c9;
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏥 しむら小児科 事前予約")
st.caption("前日の夜にセットし、画面をつけたまま充電して寝てください。")

# --- 1. 予約設定 ---
st.subheader("1. 予約設定")

# コンテナで余白を詰める
with st.container():
    # 子供選択
    target_child_str = st.radio(
        "予約するお子様",
        ["オオムラ イブキ 様 (12979)", "オオムラ エリナ 様 (10865)"],
        index=0,
        label_visibility="collapsed"
    )

    # 時間選択
    target_time_str = st.selectbox(
        "予約希望時間",
        [f"{h:02d}:{m:02d}" for h in range(9, 18) for m in [0, 15, 30, 45] 
         if not (h == 12 and m > 0) and not (h > 12 and h < 15) and not (h == 17 and m > 30)],
        index=0
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

# --- 2. 予約実行 ---
st.subheader("予約実行")

if st.button("🌙 おやすみ前セット（待機開始）"):
    
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
    
    # --- Phase 1: 待機 (ロングスリープ) ---
    status_placeholder.markdown(f"""
        <div class="status-box">
            <h3 style="margin:0; font-size:1rem; color:#4CAF50;">✅ セット完了</h3>
            <p style="margin:0; color:#555;"><b>{login_start_dt.strftime('%H:%M')}</b> に先行ログインします。</p>
            <p style="color:#d32f2f; font-weight:bold; margin-top:0.5rem; font-size:0.9rem;">⚠️ 画面を消さないでください</p>
        </div>
    """, unsafe_allow_html=True)
    
    while True:
        now = datetime.datetime.now(jst)
        wait_sec = (login_start_dt - now).total_seconds()
        
        if wait_sec <= 0:
            break
            
        if wait_sec > 60:
            time.sleep(10)
        else:
            time.sleep(1)

    # --- Phase 2: 先行ログイン & 待機 ---
    status_placeholder.markdown("""
        <div class="status-box">
            <h3 style="margin:0; font-size:1rem; color:#4CAF50;">🚀 先行ログイン中...</h3>
        </div>
    """, unsafe_allow_html=True)
    
    driver = None
    try:
        driver = get_driver()
        wait = WebDriverWait(driver, 20)
        
        # サイトアクセス & ログイン
        driver.get(START_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        try:
            driver.find_element(By.XPATH, f"//label[contains(., '{TARGET_ID}')]").click()
            driver.find_element(By.XPATH, "//button[contains(., 'ログイン')]").click()
            st.toast(f"✅ 先行ログイン成功")
        except:
            pass

        # 待機ループ
        while True:
            now = datetime.datetime.now(jst)
            remaining = (target_dt - now).total_seconds()
            
            if remaining <= 10:
                break
            
            status_placeholder.markdown(f"""
                <div class="status-box">
                    <h3 style="margin:0; font-size:1rem; color:#4CAF50;">🕒 6:00 待機中...</h3>
                    <p style="margin:0; color:#555;">あと <b>{int(remaining)}</b> 秒</p>
                </div>
            """, unsafe_allow_html=True)
            
            _ = driver.current_url 
            time.sleep(1)

        # --- Phase 3: ロケットダッシュ ---
        status_placeholder.markdown("""
            <div class="status-box" style="background-color:#ffebee; border-color:#ffcdd2;">
                <h3 style="margin:0; font-size:1rem; color:#d32f2f !important;">🔥 連打開始！</h3>
            </div>
        """, unsafe_allow_html=True)
        
        while True:
            try:
                btns = driver.find_elements(By.XPATH, "//button[contains(., '予 約') or contains(., '予約')]")
                if btns:
                    btns[0].click()
                    break
                else:
                    driver.refresh()
                    time.sleep(0.5)
            except:
                driver.refresh()
            
            if (datetime.datetime.now(jst) - target_dt).total_seconds() > 60:
                raise Exception("予約ボタン見つからず")

        # --- Phase 4: 予約ステップ ---
        # 1. 時間帯
        time_band_xpath = f"//td[contains(., '{TARGET_H_JP}')]/following-sibling::td/a[contains(., '〇') or contains(., '△')]"
        wait.until(EC.element_to_be_clickable((By.XPATH, time_band_xpath))).click()
        
        # 2. 詳細時間
        detail_time_xpath = f"//td[contains(., '{TARGET_M_JP}')]/following-sibling::td/a[contains(., '〇') or contains(., '△')]"
        wait.until(EC.element_to_be_clickable((By.XPATH, detail_time_xpath))).click()
        
        # 3. 確認へ
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '確認') or contains(., '次へ') or @type='submit']")))
        driver.execute_script("arguments[0].scrollIntoView();", next_btn)
        next_btn.click()
        
        # 4. 最終確定 (★本番有効★)
        final_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '予 約')]")))
        final_btn.click()
        
        st.balloons()
        status_placeholder.success("🏆 予約完了！")
        time.sleep(1)
        st.image(driver.get_screenshot_as_png())

    except Exception as e:
        st.error(f"エラー: {e}")
        if driver:
            st.image(driver.get_screenshot_as_png())
    finally:
        if driver:
            driver.quit()
