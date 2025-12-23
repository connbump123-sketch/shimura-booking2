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

# --- セッション状態の初期化 ---
if 'step' not in st.session_state:
    st.session_state.step = 'input'
if 'target_child_val' not in st.session_state:
    st.session_state.target_child_val = 0
if 'target_time_val' not in st.session_state:
    st.session_state.target_time_val = 0
if 'show_cancel_confirm' not in st.session_state:
    st.session_state.show_cancel_confirm = False

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
    /* 全体フォント設定 */
    @import url('https://fonts.googleapis.com/css2?family=Kosugi+Maru&display=swap');
    html, body, [class*="css"], font, span, div, p, h1, h2, h3, h4, h5, h6, button, input, select, label {
        font-family: 'Kosugi Maru', "Hiragino Maru Gothic ProN", "HGMaruGothicMPRO", "Yu Gothic Medium", "Yu Gothic", sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }

    /* レイアウト設定 */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 20rem !important; 
        max-width: 100% !important;
    }
    div[data-testid="column"] { padding: 0 !important; }
    
    /* キャプション */
    div[data-testid="stCaptionContainer"] p {
        font-size: 0.9rem !important;
        color: #555555 !important;
        text-align: center;
        margin-top: -0.5rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* 見出し設定 */
    h3 {
        font-size: 1.1rem !important;
        font-weight: bold !important;
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
        color: #555555 !important;
    }
    
    /* ボタン共通設定 */
    div.stButton > button {
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100% !important;
        padding: 0.8em 0 !important;
        font-size: 1.0rem !important;
        white-space: nowrap !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
    }
    div.stButton > button:active {
        transform: translateY(2px);
        box-shadow: none !important;
    }
    
    /* 予約内容確認ボックス */
    .info-card {
        background-color: #f8fcf8;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .info-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
        border-bottom: 1px dashed #eee;
        padding-bottom: 0.3rem;
    }
    .info-label { font-weight: bold; color: #666; }
    .info-val { font-weight: bold; color: #333; font-size: 1.1rem; }

    .stApp { background-color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# --- ヘッダー ---
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
st.markdown("""
    <h1 style='text-align: center; color: #555555; font-size: 1.2rem; margin-top: -10px; margin-bottom: 5px; line-height: 1.4;'>
        事前予約アプリ
        <div style='font-size: 0.9rem; margin-top: 5px;'>〜大村家 専用〜</div>
    </h1>
""", unsafe_allow_html=True)

st.caption("前日のうちに予約できます！")

# ==========================================
#  ロジック定義
# ==========================================

CHILD_OPTIONS = ["オオムラ イブキ 様 (12979)", "オオムラ エリナ 様 (10865)"]
TIME_OPTIONS = [f"{h:02d}:{m:02d}" for h in range(9, 18) for m in [0, 15, 30, 45] 
                if not (h == 12 and m > 0) and not (h > 12 and h < 15) and not (h == 17 and m > 30)]

# --- Step 1: 入力画面 ---
if st.session_state.step == 'input':
    st.subheader("1. 予約設定")
    with st.container():
        target_child_str = st.radio(
            "予約するお子様",
            CHILD_OPTIONS,
            index=st.session_state.target_child_val,
            label_visibility="collapsed"
        )
        st.write("")
        st.markdown('<div style="font-size: 1.1rem; font-weight: bold; color: #555555; margin-bottom: 0.3rem;">2. 予約希望時間</div>', unsafe_allow_html=True)
        target_time_str = st.selectbox(
            "予約希望時間（ラベル非表示）",
            TIME_OPTIONS,
            index=st.session_state.target_time_val,
            label_visibility="collapsed"
        )

    # 次へボタン（ピンク）
    st.markdown('<style>div.stButton > button {background-color: #f6adad !important; color: white !important;}</style>', unsafe_allow_html=True)
    if st.button("🌙 おやすみ前セット（確認へ）"):
        st.session_state.target_child_val = CHILD_OPTIONS.index(target_child_str)
        st.session_state.target_time_val = TIME_OPTIONS.index(target_time_str)
        st.session_state.step = 'confirm'
        st.session_state.show_cancel_confirm = False
        st.rerun()

# --- Step 2: 確認画面（セーフティネット） ---
elif st.session_state.step == 'confirm':
    
    # CSS: 左ボタン(ピンク)と右ボタン(緑)を分けるためのスタイル
    st.markdown("""
    <style>
    /* 左のカラムのボタン (訂正/戻る) -> ピンク */
    div[data-testid="column"]:nth-of-type(1) div.stButton > button {
        background-color: #f6adad !important;
        color: white !important;
    }
    /* 右のカラムのボタン (開始/続行) -> 緑 */
    div[data-testid="column"]:nth-of-type(2) div.stButton > button {
        background-color: #4CAF50 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 警告メッセージ
    if st.session_state.show_cancel_confirm:
         st.error("🛑 本当に設定を取り消して、最初の画面に戻りますか？")
    else:
         st.warning("⚠️ 画面がスリープにならないように設定してから寝てね！")

    # 予約内容の表示
    selected_child = CHILD_OPTIONS[st.session_state.target_child_val]
    selected_time = TIME_OPTIONS[st.session_state.target_time_val]
    
    st.markdown(f"""
        <div class="info-card">
            <h3 style="margin-top:0; border-bottom:2px solid #4CAF50; padding-bottom:5px;">📋 予約内容の確認</h3>
            <div class="info-row" style="margin-top:10px;">
                <span class="info-label">予約者</span>
                <span class="info-val">{selected_child.split(' ')[0]} {selected_child.split(' ')[1]}</span>
            </div>
            <div class="info-row" style="border-bottom:none;">
                <span class="info-label">希望時間</span>
                <span class="info-val" style="color:#e91e63; font-size:1.4rem;">{selected_time}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- 操作ボタンエリア（横並び） ---
    col1, col2 = st.columns(2)
    
    # 分岐処理
    if st.session_state.show_cancel_confirm:
        # 【確認モード】
        with col1:
            if st.button("はい (戻る)"):
                st.session_state.step = 'input'
                st.session_state.show_cancel_confirm = False
                st.rerun()
        with col2:
            if st.button("いいえ (続行)"):
                st.session_state.show_cancel_confirm = False
                st.rerun()
    else:
        # 【通常モード】
        with col1:
            if st.button("訂正する"):
                st.session_state.show_cancel_confirm = True
                st.rerun()
        with col2:
            if st.button("🚀 待機開始"):
                st.session_state.step = 'running'
                st.rerun()


# --- Step 3: 実行画面（ループ突入） ---
elif st.session_state.step == 'running':
    
    selected_child = CHILD_OPTIONS[st.session_state.target_child_val]
    selected_time = TIME_OPTIONS[st.session_state.target_time_val]
    
    TARGET_ID = "12979" if "12979" in selected_child else "10865"
    TARGET_NAME = "イブキ" if "イブキ" in selected_child else "エリナ"
    TARGET_H = selected_time.split(':')[0]
    TARGET_M = selected_time.split(':')[1]
    TARGET_H_JP = f"{int(TARGET_H)}時"
    TARGET_M_JP = f"{TARGET_H}時{TARGET_M}分"
    START_URL = "https://shimura-kids.com/yoyaku/php/line_login.php"

    st.warning("⚠️ 待機中はボタン操作ができません。中止する場合はブラウザを再読み込みしてください。")
    
    status_placeholder = st.empty()

    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.datetime.now(jst)
    target_dt = now.replace(hour=6, minute=0, second=0, microsecond=0)
    if now.hour >= 6:
        target_dt += datetime.timedelta(days=1)
    
    login_start_dt = target_dt - datetime.timedelta(minutes=10)

    # Phase 1: 待機
    status_placeholder.markdown(f"""
        <div style="padding:1.5rem; border-radius:10px; background-color:#e8f5e9; border:2px solid #4CAF50; text-align:center;">
            <h2 style="margin:0; color:#2e7d32;">💤 待機中...</h2>
            <p style="font-size:1.2rem; margin:10px 0;"><b>{login_start_dt.strftime('%H:%M')}</b> に先行ログインします</p>
            <p style="margin:0; color:#555;">予約: {TARGET_NAME} 様 ({selected_time})</p>
        </div>
    """, unsafe_allow_html=True)
    
    while True:
        now = datetime.datetime.now(jst)
        wait_sec = (login_start_dt - now).total_seconds()
        if wait_sec <= 0: break
        if wait_sec > 60: time.sleep(10)
        else: time.sleep(1)

    # Phase 2: 先行ログイン
    status_placeholder.info("🚀 先行ログインを実行中...")
    
    def get_driver():
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1')
        return webdriver.Chrome(options=options)

    driver = None
    try:
        driver = get_driver()
        wait = WebDriverWait(driver, 20)
        driver.get(START_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        try:
            driver.find_element(By.XPATH, f"//label[contains(., '{TARGET_ID}')]").click()
            driver.find_element(By.XPATH, "//button[contains(., 'ログイン')]").click()
        except:
            pass

        while True:
            now = datetime.datetime.now(jst)
            remaining = (target_dt - now).total_seconds()
            if remaining <= 10: break
            status_placeholder.markdown(f"### 🕒 6:00 開門待ち... あと {int(remaining)} 秒")
            _ = driver.current_url 
            time.sleep(1)

        status_placeholder.warning("🔥 予約処理を開始します！")
        
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

        time_band_xpath = f"//td[contains(., '{TARGET_H_JP}')]/following-sibling::td/a[contains(., '〇') or contains(., '△')]"
        wait.until(EC.element_to_be_clickable((By.XPATH, time_band_xpath))).click()
        
        detail_time_xpath = f"//td[contains(., '{TARGET_M_JP}')]/following-sibling::td/a[contains(., '〇') or contains(., '△')]"
        wait.until(EC.element_to_be_clickable((By.XPATH, detail_time_xpath))).click()
        
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '確認') or contains(., '次へ') or @type='submit']")))
        driver.execute_script("arguments[0].scrollIntoView();", next_btn)
        next_btn.click()
        
        final_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '予 約')]")))
        
        # 👇 本番稼働時はコメントアウトを外す
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
