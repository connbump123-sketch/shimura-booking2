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
    
    /* 全体のフォント統一 */
    html, body, [class*="css"] {
        font-family: 'Kosugi Maru', sans-serif !important;
    }

    /* 背景色固定 (ダークモード対策) */
    .stApp {
        background-color: #ffffff !important;
    }
    
    /* 基本文字色 */
    h1, h2, h3, p, div, label, span {
        color: #555555 !important;
    }

    /* レイアウト調整：上部余白 */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important; 
    }

    /* タイトルまわりの調整 */
    h1 {
        font-size: 1.1rem !important;
        margin-top: 0 !important;
        line-height: 1.4 !important;
    }
    div[data-testid="stCaptionContainer"] p {
        font-size: 0.85rem !important;
        color: #888888 !important;
    }
    
    /* ロゴ画像の調整 */
    div[data-testid="stImage"] {
        display: flex;
        justify-content: center;
        /* ★修正点: 空白を半分くらいに狭めた */
        margin-bottom: 0.2rem !important;
    }
    div[data-testid="stImage"] img {
        max-width: 80% !important;
    }

    /* ----------------------------------
       ボタンのデザイン修正
    ---------------------------------- */
    /* 共通設定 */
    div.stButton > button {
        width: 100%;
        border-radius: 8px !important;
        font-weight: bold !important;
        padding: 0.6rem !important;
        font-size: 1rem !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
    }

    /* Primaryボタン（ピンク：開始用） */
    button[kind="primary"] {
        background-color: #f6adad !important;
        border: none !important;
        color: white !important;
    }
    button[kind="primary"] * {
        color: white !important;
    }

    /* ★修正点: Secondaryボタン（濃いグレー背景・白文字：訂正用） */
    button[kind="secondary"] {
        background-color: #666666 !important; /* 濃いグレー */
        border: none !important;
        color: white !important; /* 白文字 */
    }
    button[kind="secondary"] * {
        color: white !important;
    }

    /* ----------------------------------
       入力フォームのデザイン
    ---------------------------------- */
    /* ラジオボタン */
    div[role="radiogroup"] label > div:first-child {
        background-color: #fff !important;
        border: 2px solid #ddd !important;
    }
    div[role="radiogroup"] label:has(input:checked) > div:first-child {
        background-color: #4CAF50 !important;
        border-color: #4CAF50 !important;
    }
    div[role="radiogroup"] label:has(input:checked) p {
        color: #4CAF50 !important;
        font-weight: bold !important;
    }

    /* ドロップダウンリスト (本体: 緑背景・白文字) */
    div[data-baseweb="select"] > div {
        background-color: #556b2f !important;
        border-color: #556b2f !important;
        color: white !important;
    }
    div[data-baseweb="select"] span, div[data-baseweb="select"] svg {
        color: white !important;
        fill: white !important;
    }
    
    /* ポップアップメニューの外枠 */
    div[data-baseweb="popover"] div[role="listbox"] {
        background-color: #556b2f !important;
    }
    /* ★修正点: リスト内の候補（モスグリーン背景・白文字） */
    div[data-baseweb="popover"] li {
        background-color: #556b2f !important; /* 背景色を追加 */
        color: white !important;
    }
    /* ホバー時 */
    div[data-baseweb="popover"] li:hover {
        background-color: #3b4a1c !important;
    }

    /* ----------------------------------
       情報ボックスのデザイン
    ---------------------------------- */
    /* 警告ボックス（黄色） */
    .info-box-yellow {
        background-color: #fff9c4;
        border: 1px solid #fff59d;
        padding: 0.8rem;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 1rem;
        color: #f57f17 !important;
        font-weight: bold;
        font-size: 0.9rem;
        /* ★修正点: 改行を許可するために nowrap を削除 */
    }

    /* 待機ボックス（緑） */
    .status-box-green {
        background-color: #e8f5e9;
        border: 2px solid #4CAF50;
        /* ★修正点: 上下のパディングを少し狭めた */
        padding: 1rem 0.5rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
        color: #1b5e20 !important;
    }
    
    /* 案内ボックス（青） */
    .info-box-blue {
        background-color: #e3f2fd;
        border: 1px solid #90caf9;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 1rem;
        color: #0d47a1 !important;
        font-weight: bold;
    }

    /* 確認カード */
    .confirm-card {
        background-color: #f9f9f9;
        border: 1px solid #eee;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .card-row {
        display: flex;
        justify-content: space-between;
        border-bottom: 1px dashed #ddd;
        padding: 0.5rem 0;
    }
    .card-row:last-child { border-bottom: none; }
    .card-label { font-weight: bold; color: #666; }
    .card-value { font-weight: bold; color: #333; font-size: 1.1rem; }

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
    <h1 style='text-align: center;'>
        事前予約アプリ
        <div style='font-size: 0.85rem; margin-top: 5px; color: #666;'>〜大村家 専用〜</div>
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
    # type="primary"でピンク色ボタン
    if st.button("🌙 おやすみ前セット（確認へ）", type="primary"):
        st.session_state.target_child_val = CHILD_OPTIONS.index(target_child_str)
        st.session_state.target_time_val = TIME_OPTIONS.index(target_time_str)
        st.session_state.step = 'confirm'
        st.rerun()

# --- Step 2: 確認画面 ---
elif st.session_state.step == 'confirm':
    scroll_to_top()
    
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

    # ボタン配置：左側を空けて、右側にボタンを配置
    col_l, col_r = st.columns([1, 1]) 
    
    with col_l:
        # 左下：訂正ボタン（濃いグレー）
        if st.button("訂正する", type="secondary"):
            st.session_state.step = 'input'
            st.rerun()
            
    with col_r:
        # 右下：開始ボタン（ピンク）
        if st.button("🚀 待機開始", type="primary"):
            st.session_state.step = 'running'
            st.rerun()

# --- Step 3: 待機画面 ---
elif st.session_state.step == 'running':
    scroll_to_top()
    
    selected_child = CHILD_OPTIONS[st.session_state.target_child_val]
    selected_time = TIME_OPTIONS[st.session_state.target_time_val]
    
    TARGET_ID = "12979" if "12979" in selected_child else "10865"
    TARGET_NAME = "イブキ" if "イブキ" in selected_child else "エリナ"
    TARGET_H = selected_time.split(':')[0]
    TARGET_M = selected_time.split(':')[1]
    TARGET_H_JP = f"{int(TARGET_H)}時"
    TARGET_M_JP = f"{TARGET_H}時{TARGET_M}分"
    START_URL = "https://shimura-kids.com/yoyaku/php/line_login.php"

    # ★修正点: 黄色ボックス（「設定」で改行）
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

    # ★修正点: 待機ボックス（内部の隙間を狭めた）
    status_placeholder.markdown(f"""
        <div class="status-box-green">
            <h2 style="margin:0; color:#2e7d32 !important; white-space: nowrap; font-size: 1.4rem;">💤 待機中...</h2>
            <p style="font-size:1rem; margin: 5px 0; white-space: nowrap;"><b>{login_start_dt.strftime('%H:%M')}</b> に先行ログインします</p>
            <hr style="border-top: 1px dashed #4CAF50; margin: 5px 0;">
            <p style="margin:0; white-space: nowrap;">予約: <b>{TARGET_NAME}</b> 様 ({selected_time})</p>
        </div>
    """, unsafe_allow_html=True)

    st.write("")
    
    # 待機中の訂正ボタン（左配置・濃いグレー）
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("訂正・中止する", type="secondary"):
            st.session_state.step = 'input'
            st.rerun()
    with col2:
        st.empty() # 右は空ける
            
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
