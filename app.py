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
import streamlit.components.v1 as components

# --- セッション状態の初期化 ---
if 'step' not in st.session_state:
    st.session_state.step = 'input'
if 'target_child_val' not in st.session_state:
    st.session_state.target_child_val = 0
if 'target_time_val' not in st.session_state:
    st.session_state.target_time_val = 0

# --- ページ設定 ---
st.set_page_config(
    page_title="しむら小児科予約",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- スクロール関数 ---
def scroll_to_top():
    js = '''
    <script>
        var body = window.parent.document.body;
        var attempts = 0;
        function scrollToTop() {
            body.scrollTop = 0;
            if (body.scrollTop !== 0 && attempts < 10) {
                attempts++;
                setTimeout(scrollToTop, 10);
            }
        }
        scrollToTop();
    </script>
    '''
    components.html(js, height=0)

# --- デザイン調整 (CSS) ---
st.markdown("""
    <style>
    /* フォント設定 */
    @import url('https://fonts.googleapis.com/css2?family=Kosugi+Maru&display=swap');
    
    /* ============================
       1. ダークモード根絶 & 基本設定
    ============================ */
    :root {
        color-scheme: light only !important;
    }
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #ffffff !important;
        font-family: 'Kosugi Maru', sans-serif !important;
        color: #555555 !important;
    }
    
    /* レイアウト調整：上部余白を大幅に増やしてロゴ隠れを防止 */
    .block-container {
        padding-top: 4rem !important; /* ★ここを増やしました★ */
        padding-bottom: 5rem !important; 
        max-width: 100% !important;
    }

    /* タイトル調整 */
    h1 {
        font-size: 1.1rem !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0 !important;
        color: #555555 !important;
    }
    div[data-testid="stCaptionContainer"] p {
        font-size: 0.85rem !important;
        margin-top: 0 !important;
        color: #666666 !important;
    }
    
    /* ロゴ画像を中央寄せ */
    div[data-testid="stImage"] {
        display: flex;
        justify-content: center;
    }
    div[data-testid="stImage"] img {
        max-width: 80% !important;
    }

    /* ============================
       2. スマホでのボタン横並び強制設定（はみ出し防止）
    ============================ */
    div[data-testid="column"] {
        width: 48% !important; /* 50%だと隙間で溢れるので48%に */
        flex: 1 1 auto !important;
        min-width: 0 !important; /* 最小幅制限を解除 */
        padding: 0 4px !important;
    }
    
    /* ============================
       3. 入力フォームのデザイン
    ============================ */
    /* ラジオボタン */
    div[role="radiogroup"] label:not(:has(input:checked)) p { color: #cccccc !important; }
    div[role="radiogroup"] label:not(:has(input:checked)) > div:first-child {
        border: 2px solid #e0e0e0 !important; background-color: #fafafa !important;
    }
    /* 選択時グリーン */
    div[role="radiogroup"] label:has(input:checked) p { 
        color: #4CAF50 !important; 
        font-weight: bold !important; 
    }
    div[role="radiogroup"] label:has(input:checked) > div:first-child {
        border-color: #4CAF50 !important; 
        background-color: #4CAF50 !important;
    }
    div[role="radiogroup"] label:has(input:checked) > div:first-child svg { 
        fill: #ffffff !important; 
    }

    /* ドロップダウンリスト（物理的強制） */
    div[data-baseweb="select"] > div {
        background-color: #556b2f !important; 
        border-color: #556b2f !important; 
        color: #ffffff !important;
    }
    /* ★中身の全要素を白に強制★ */
    div[data-baseweb="select"] * { 
        color: #ffffff !important; 
        fill: #ffffff !important; 
    }
    
    /* ポップアップメニュー */
    div[data-baseweb="popover"] div[role="listbox"], div[data-baseweb="popover"] ul {
        background-color: #556b2f !important;
    }
    div[data-baseweb="popover"] * {
        color: #ffffff !important;
    }
    div[data-baseweb="popover"] li:hover {
        background-color: #3b4a1c !important;
    }

    /* ============================
       4. ボタンの基本デザイン（黒化防止）
    ============================ */
    div.stButton > button {
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100% !important;
        padding: 0.8em 0 !important;
        font-size: 0.95rem !important;
        white-space: nowrap !important;
        border: none !important;
    }
    
    /* ============================
       5. 情報ボックスのデザイン
    ============================ */
    .info-box-blue {
        background-color: #e3f2fd;
        border: 1px solid #90caf9;
        color: #0d47a1 !important;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    /* 警告ボックス (文字色オレンジ) */
    .info-box-yellow {
        background-color: #fff9c4;
        border: 1px solid #fff59d;
        color: #f57f17 !important; 
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .status-box-green {
        background-color: #e8f5e9;
        border: 2px solid #4CAF50;
        color: #1b5e20 !important;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .confirm-card {
        background-color: #f9f9f9;
        border: 1px solid #eee;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1.5rem;
    }
    .card-row {
        display: flex;
        justify-content: space-between;
        border-bottom: 1px dashed #ddd;
        padding: 0.5rem 0;
    }
    .card-row:last-child { border-bottom: none; }
    .card-label { color: #666 !important; font-weight: bold; }
    .card-value { color: #333 !important; font-weight: bold; font-size: 1.1rem; }
    
    </style>
""", unsafe_allow_html=True)

# --- ヘッダー（ロゴ） ---
logo_file = None
if os.path.exists("logo.png"): logo_file = "logo.png"
elif os.path.exists("logo.jpg"): logo_file = "logo.jpg"
elif os.path.exists("logo.jpeg"): logo_file = "logo.jpeg"

if logo_file:
    st.image(logo_file, width=300) 
else:
    st.error("ロゴ画像なし")

# --- タイトル ---
st.markdown("""
    <h1 style='text-align: center; margin-top: -5px; line-height: 1.3;'>
        事前予約アプリ
        <div style='font-size: 0.85rem; margin-top: 3px; color: #666666 !important;'>〜大村家 専用〜</div>
    </h1>
""", unsafe_allow_html=True)

# ==========================================
#  ロジック定義
# ==========================================

CHILD_OPTIONS = ["オオムラ イブキ 様 (12979)", "オオムラ エリナ 様 (10865)"]
TIME_OPTIONS = [f"{h:02d}:{m:02d}" for h in range(9, 18) for m in [0, 15, 30, 45] 
                if not (h == 12 and m > 0) and not (h > 12 and h < 15) and not (h == 17 and m > 30)]

# --- Step 1: 入力画面 ---
if st.session_state.step == 'input':
    # ★Step1専用：ピンクボタンの中身を完全に白にする★
    st.markdown("""
        <style>
        div.stButton > button {
            background-color: #f6adad !important;
            color: #ffffff !important;
            border: none !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        }
        /* ボタンの中の全ての要素を白にする */
        div.stButton > button * {
            color: #ffffff !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.caption("前日のうちに予約できます！")
    
    st.subheader("1. 予約設定")
    with st.container():
        target_child_str = st.radio(
            "予約するお子様",
            CHILD_OPTIONS,
            index=st.session_state.target_child_val,
            label_visibility="collapsed"
        )
        st.write("")
        st.markdown('<div style="font-weight:bold; color:#555; margin-bottom:0.3rem;">2. 予約希望時間</div>', unsafe_allow_html=True)
        target_time_str = st.selectbox(
            "予約希望時間",
            TIME_OPTIONS,
            index=st.session_state.target_time_val,
            label_visibility="collapsed"
        )

    st.write("")
    if st.button("🌙 おやすみ前セット（確認へ）"):
        st.session_state.target_child_val = CHILD_OPTIONS.index(target_child_str)
        st.session_state.target_time_val = TIME_OPTIONS.index(target_time_str)
        st.session_state.step = 'confirm'
        st.rerun()

# --- Step 2: 確認画面 ---
elif st.session_state.step == 'confirm':
    scroll_to_top()
    
    # ★Step2専用：ボタン配置＆色設定（中身まで指定）★
    st.markdown("""
        <style>
        /* 左右分割 */
        div[data-testid="column"] {
            width: 48% !important; /* はみ出し防止 */
            flex: 1 1 auto !important;
            min-width: 0 !important;
            padding: 0 4px !important;
        }
        /* 左ボタン：白背景・黒文字 */
        div[data-testid="column"]:nth-of-type(1) div.stButton > button {
            background-color: #ffffff !important;
            color: #555555 !important;
            border: 1px solid #cccccc !important;
        }
        div[data-testid="column"]:nth-of-type(1) div.stButton > button * {
            color: #555555 !important;
        }
        
        /* 右ボタン：ピンク背景・白文字 */
        div[data-testid="column"]:nth-of-type(2) div.stButton > button {
            background-color: #f6adad !important;
            color: #ffffff !important;
            border: none !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        }
        div[data-testid="column"]:nth-of-type(2) div.stButton > button * {
            color: #ffffff !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="info-box-blue">
            まだ予約は始まっていません。<br>下のボタンで待機を開始してください。
        </div>
    """, unsafe_allow_html=True)

    selected_child = CHILD_OPTIONS[st.session_state.target_child_val]
    selected_time = TIME_OPTIONS[st.session_state.target_time_val]
    
    st.markdown(f"""
        <div class="confirm-card">
            <div style="text-align:center; font-weight:bold; border-bottom:2px solid #4CAF50; margin-bottom:10px; padding-bottom:5px; color:#555;">📋 予約内容の確認</div>
            <div class="card-row">
                <span class="card-label">予約者</span>
                <span class="card-value">{selected_child.split(' ')[0]} {selected_child.split(' ')[1]}</span>
            </div>
            <div class="card-row">
                <span class="card-label">希望時間</span>
                <span class="card-value" style="color:#e91e63 !important; font-size:1.3rem;">{selected_time}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("訂正する"):
            st.session_state.step = 'input'
            st.rerun()
    with col2:
        if st.button("🚀 待機開始"):
            st.session_state.step = 'running'
            st.rerun()

# --- Step 3: 待機画面 ---
elif st.session_state.step == 'running':
    scroll_to_top()
    
    # ★Step3専用：訂正ボタン(白)CSSを注入★
    st.markdown("""
        <style>
        div.stButton > button {
            background-color: #ffffff !important;
            color: #555555 !important;
            border: 1px solid #cccccc !important;
        }
        div.stButton > button * {
            color: #555555 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    selected_child = CHILD_OPTIONS[st.session_state.target_child_val]
    selected_time = TIME_OPTIONS[st.session_state.target_time_val]
    
    TARGET_ID = "12979" if "12979" in selected_child else "10865"
    TARGET_NAME = "イブキ" if "イブキ" in selected_child else "エリナ"
    TARGET_H = selected_time.split(':')[0]
    TARGET_M = selected_time.split(':')[1]
    TARGET_H_JP = f"{int(TARGET_H)}時"
    TARGET_M_JP = f"{TARGET_H}時{TARGET_M}分"
    START_URL = "https://shimura-kids.com/yoyaku/php/line_login.php"

    st.markdown("""
        <div class="info-box-yellow">
            ⚠️ 画面がスリープにならないように<br>設定してから寝てね！
        </div>
    """, unsafe_allow_html=True)

    status_placeholder = st.empty()

    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.datetime.now(jst)
    target_dt = now.replace(hour=6, minute=0, second=0, microsecond=0)
    if now.hour >= 6:
        target_dt += datetime.timedelta(days=1)
    login_start_dt = target_dt - datetime.timedelta(minutes=10)

    status_placeholder.markdown(f"""
        <div class="status-box-green">
            <h2 style="margin:0; color:#2e7d32 !important;">💤 待機中...</h2>
            <p style="font-size:1.1rem; margin:10px 0;"><b>{login_start_dt.strftime('%H:%M')}</b> に先行ログインします</p>
            <hr style="border-top: 1px dashed #4CAF50;">
            <p style="margin:0;">予約: <b>{TARGET_NAME}</b> 様 ({selected_time})</p>
        </div>
    """, unsafe_allow_html=True)

    st.write("")
    if st.button("訂正・中止する"):
        st.session_state.step = 'input'
        st.rerun()
    st.caption("※ 反応しない場合はブラウザを再読み込みしてください")

    while True:
        now = datetime.datetime.now(jst)
        wait_sec = (login_start_dt - now).total_seconds()
        if wait_sec <= 0: break
        time.sleep(1)

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
