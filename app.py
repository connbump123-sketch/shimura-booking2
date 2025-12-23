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
    /* 1. 全体のレイアウトをコンパクトに（1画面に収める） */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }
    
    /* 2. タイトルのサイズ縮小 */
    h1 {
        font-size: 1.4rem !important;
        margin-bottom: 0.2rem !important;
        color: #444444 !important;
    }
    p {
        font-size: 0.9rem !important;
        margin-bottom: 0.5rem !important;
        color: #666666 !important;
    }
    
    /* 3. 見出しの調整 */
    h3 {
        font-size: 1.1rem !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.2rem !important;
        padding: 0 !important;
        color: #4CAF50 !important; /* 緑色 */
    }
    
    /* 4. ラジオボタンのデザイン変更 (緑基調) */
    /* 選択されていない状態（グレー） */
    div[role="radiogroup"] label span {
        color: #555555 !important; /* 濃いグレー */
        font-weight: bold !important;
    }
    /* 選択された状態（緑枠・中白） */
    div[role="radiogroup"] div[aria-checked="true"] {
        background-color: #ffffff !important;
        border: 2px solid #4CAF50 !important; /* 緑の枠 */
    }
    div[role="radiogroup"] div[aria-checked="true"] > div {
        background-color: #4CAF50 !important; /* 中の点も緑 */
    }
    /* 未選択の丸（グレー） */
    div[role="radiogroup"] div[aria-checked="false"] {
        border: 2px solid #9e9e9e !important; /* 薄いグレー */
        background-color: #ffffff !important;
    }

    /* 5. 実行ボタン（ピンク） */
    div.stButton > button {
        background-color: #f6adad !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100% !important; /* 幅いっぱいに */
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
        "予約するお子様", # ラベルは非表示設定不可だがCSSで調整済
        ["オオムラ イブキ 様 (12979)", "オオムラ エリナ 様 (10865)"],
        index=0,
        label_visibility="collapsed" # ラベルを隠してコンパクトに
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
            <h3 style="margin:0; font-size:1rem;">✅ セット完了</h3>
            <p style="margin:0;"><b>{login_start_dt.strftime('%H:%M')}</b> に先行ログインします。</p>
            <p style="color:red; font-weight:bold; margin-top:0.5rem;">⚠️ 画面を消さないで！</p>
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
            <h3 style="margin:0; font-size:1rem;">🚀 先行ログイン中...</h3>
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
                    <h3 style="margin:0; font-size:1rem;">🕒 6:00 待機中...</h3>
                    <p style="margin:0;">あと <b>{int(remaining)}</b> 秒</p>
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
