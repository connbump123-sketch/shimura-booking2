import streamlit as st
import time
import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os

# --- ページ設定 ---
st.set_page_config(
    page_title="しむら小児科予約",
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
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 20rem !important; 
        max-width: 100% !important;
    }
    
    div[data-testid="column"] { padding: 0 !important; }

    /* キャプションの設定 */
    div[data-testid="stCaptionContainer"] p {
        font-size: 0.9rem !important;
        color: #555555 !important;
        text-align: center;
        margin-top: -0.5rem !important;
        margin-bottom: 0.5rem !important;
        line-height: 1.2 !important;
    }

    /* 見出し設定 */
    h3 {
        font-size: 1.1rem !important;
        font-weight: bold !important;
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
        padding-top: 0 !important;
        color: #555555 !important;
    }
    
    .custom-label {
        font-size: 1.1rem;
        font-weight: bold;
        color: #555555;
        margin-bottom: 0.3rem;
        font-family: 'Kosugi Maru', sans-serif;
    }

    /* 入力フォーム設定 */
    div[role="radiogroup"] label:not(:has(input:checked)) p { color: #cccccc !important; }
    div[role="radiogroup"] label:not(:has(input:checked)) > div:first-child {
        border: 2px solid #e0e0e0 !important; background-color: #fafafa !important;
    }
    div[role="radiogroup"] label:has(input:checked) p { color: #4CAF50 !important; font-weight: bold !important; }
    div[role="radiogroup"] label:has(input:checked) > div:first-child {
        border-color: #4CAF50 !important; background-color: #4CAF50 !important;
    }
    div[role="radiogroup"] label:has(input:checked) > div:first-child svg { fill: #ffffff !important; }
    div[role="radiogroup"] p { font-size: 1rem !important; }

    div[data-baseweb="select"] > div {
        background-color: #556b2f !important; border-color: #556b2f !important; color: #ffffff !important;
    }
    div[data-baseweb="select"] span { color: #ffffff !important; font-size: 1rem !important; }
    div[data-baseweb="select"] svg { fill: #ffffff !important; }
    
    /* 実行ボタン設定 */
    div.stButton > button {
        background-color: #f6adad !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100% !important;
        padding: 0.8em 0 !important;
        margin-top: 1rem !important;
        font-size: 1.1rem !important;
        white-space: nowrap !important;
    }
    
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

# --- タイトル ---
st.markdown("""
    <h1 style='text-align: center; color: #555555; font-size: 1.2rem; margin-top: -10px; margin-bottom: 5px; line-height: 1.4;'>
        事前予約アプリ
        <div style='font-size: 0.9rem; margin-top: 5px;'>〜大村家 専用〜</div>
    </h1>
""", unsafe_allow_html=True)

# キャプション
st.caption("前日のうちに予約できます！")

# --- 1. 予約設定 ---
st.subheader("1. 予約設定")

with st.container():
    target_child_str = st.radio(
        "予約するお子様",
        ["オオムラ イブキ 様 (12979)", "オオムラ エリナ 様 (10865)"],
        index=0,
        label_visibility="collapsed"
    )

    st.write("")
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

# ボタンを押すと、ここから下の処理が動きます
if st.button("🌙 おやすみ前セット（待機開始）"):
    
    # ⚠️ 注意メッセージを表示（黄色い枠）
    st.warning("⚠️ 画面がスリープにならないように設定してから寝てね！")
    
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
    # エラー回避のため、HTMLは変数に入れてから表示します
    html_content = f"""
    <div style="padding:1rem; border-radius:8px; background-color:#f1f8e9; border:1px solid #c8e6c9;">
        <h3 style="margin:0; font-size:1rem; color:#4CAF50 !important;">✅ セット完了</h3>
        <p style="margin:0; color:#555;"><b>{login_start_dt.strftime('%H:%M')}</b> に先行ログインします。</p>
    </div>
    """
    status_placeholder.markdown(html_content, unsafe_allow_html=True)
    
    # 待機ループ
    while True:
        now = datetime.datetime.now(jst)
        wait_sec = (login_start_dt - now).total_seconds()
        
        if wait_sec <= 0:
            break
            
        if wait_sec > 60:
            time.sleep(10)
        else:
            time.sleep(1)

    # --- Phase 2: 先行ログイン ---
    status_placeholder.info("🚀 先行ログインを開始します...")
    
    driver = None
    try:
        driver = get_driver()
        wait = WebDriverWait(driver, 20)
        
        # サイトへアクセス
        driver.get(START_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        try:
            # 子供選択 & ログイン
            driver.find_element(By.XPATH, f"//label[contains(., '{TARGET_ID}')]").click()
            driver.find_element(By.XPATH, "//button[contains(., 'ログイン')]").click()
            st.toast("先行ログイン成功！")
        except:
            pass

        # 6:00まで待機
        while True:
            now = datetime.datetime.now(jst)
            remaining = (target_dt - now).total_seconds()
            if remaining <= 10:
                break
            
            status_placeholder.markdown(f"### 🕒 6:00 開門待ち... あと {int(remaining)} 秒")
            _ = driver.current_url 
            time.sleep(1)

        # --- Phase 3: ロケットダッシュ ---
        status_placeholder.warning("🔥 連打モード開始！")
        
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
                raise Exception("予約ボタンが見つかりませんでした")

        # --- Phase 4: 予約ステップ ---
        # 1. 時間帯
        time_band_xpath = f"//td[contains(., '{TARGET_H_JP}')]/following-sibling::td/a[contains(., '〇') or contains(., '△')]"
        wait.until(EC.element_to_be_clickable((By.XPATH, time_band_xpath))).click()
        
        # 2. 詳細時間
        detail_time_xpath = f"//td[contains(., '{TARGET_M_JP}')]/following-sibling::td/a[contains(., '〇') or contains(., '△')]"
        wait.until(EC.element_to_be_clickable((By.XPATH, detail_time_xpath))).click()
        
        # 3. 確認画面
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '確認') or contains(., '次へ') or @type='submit']")))
        driver.execute_script("arguments[0].scrollIntoView();", next_btn)
        next_btn.click()
        
        # 4. 最終確定 (★ここだけコメントアウトしてあります★)
        final_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '予 約')]")))
        
        # 👇👇👇 本番では、下の行の「#」を消してください 👇👇👇
        # final_btn.click()
        
        st.balloons()
        st.success("🏆 予約完了！")
        st.image(driver.get_screenshot_as_png())

    except Exception as e:
        st.error(f"エラー: {e}")
        if driver:
            st.image(driver.get_screenshot_as_png())
    finally:
        if driver:
            driver.quit()
