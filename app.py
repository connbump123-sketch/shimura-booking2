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

# --- スクロール制御関数 ---
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

# --- 究極のCSSデザイン ---
st.markdown("""
    <style>
    /* 1. 強制ライトモード化 (ダークモード対策の鉄則) */
    [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
    }
    [data-testid="stHeader"] {
        background-color: #ffffff !important;
    }
    
    /* 2. 全テキストの色を「濃いグレー」に強制統一 */
    .stApp, div, p, span, h1, h2, h3, h4, h5, h6, label, li {
        color: #333333 !important;
        font-family: "Hiragino Maru Gothic ProN", "Kosugi Maru", sans-serif !important;
    }

    /* 3. レイアウト調整 (余白削減) */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 5rem !important; 
        max-width: 100% !important;
    }

    /* 4. 入力フォームの徹底スタイル */
    /* ラジオボタン */
    div[role="radiogroup"] label > div:first-child {
        background-color: #fff !important;
        border: 2px solid #ccc !important;
    }
    div[role="radiogroup"] label:has(input:checked) > div:first-child {
        background-color: #4CAF50 !important;
        border-color: #4CAF50 !important;
    }
    div[role="radiogroup"] label:has(input:checked) > div:first-child svg {
        fill: white !important;
    }
    
    /* ドロップダウン (セレクトボックス) */
    div[data-baseweb="select"] > div {
        background-color: #556b2f !important; /* モスグリーン背景 */
        border-color: #556b2f !important;
        color: white !important; /* テキスト白 */
    }
    div[data-baseweb="select"] span {
        color: white !important; /* 選択値の文字色 */
    }
    div[data-baseweb="select"] svg {
        fill: white !important; /* 矢印アイコン色 */
    }
    /* ドロップダウンのリスト中身 */
    div[data-baseweb="popover"] div, div[data-baseweb="popover"] li {
        color: white !important;
        background-color: #556b2f !important;
    }

    /* 5. ボタンデザインの基礎 (後で個別上書き) */
    div.stButton > button {
        width: 100% !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        padding: 0.8em 0 !important;
        font-size: 1rem !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }

    /* 6. 情報カードのデザイン */
    .info-card {
        background-color: #f9f9f9;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1.5rem;
    }
    .info-row {
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px dashed #ddd; padding: 0.8rem 0;
    }
    .info-row:last-child { border-bottom: none; }
    .info-label { font-size: 0.9rem; color: #666 !important; }
    .info-val { font-size: 1.1rem; font-weight: bold; color: #333 !important; }

    /* ステータスボックス */
    .status-green {
        background-color: #e8f5e9;
        border: 2px solid #4CAF50;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .status-alert {
        background-color: #fff9c4;
        border: 2px solid #fbc02d;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 1rem;
        color: #f57f17 !important;
        font-weight: bold;
    }
    .status-info {
        background-color: #e3f2fd;
        border: 1px solid #2196f3;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 1rem;
        color: #0d47a1 !important;
        font-weight: bold;
    }

    </style>
""", unsafe_allow_html=True)

# --- ヘッダー（ロゴ） ---
logo_file = None
if os.path.exists("logo.png"): logo_file = "logo.png"
elif os.path.exists("logo.jpg"): logo_file = "logo.jpg"
elif os.path.exists("logo.jpeg"): logo_file = "logo.jpeg"

col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    if logo_file:
        st.image(logo_file, use_container_width=True)
    else:
        st.error("ロゴ画像なし")

# --- タイトル ---
st.markdown("""
    <h1 style='text-align: center; margin-top: -10px; line-height: 1.4; color:#333 !important;'>
        事前予約アプリ
        <div style='font-size: 0.9rem; margin-top: 5px; color: #666 !important;'>〜大村家 専用〜</div>
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

    # Step 1 のボタン（ピンク）
    st.markdown("""
        <style>
        div.stButton > button {
            background-color: #f6adad !important;
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.write("")
    if st.button("🌙 おやすみ前セット（確認へ）"):
        st.session_state.target_child_val = CHILD_OPTIONS.index(target_child_str)
        st.session_state.target_time_val = TIME_OPTIONS.index(target_time_str)
        st.session_state.step = 'confirm'
        st.rerun()

# --- Step 2: 確認画面 ---
elif st.session_state.step == 'confirm':
    scroll_to_top()

    # 青い案内
    st.markdown("""
        <div class="status-info">
            まだ予約は始まっていません。<br>下のボタンで待機を開始してください。
        </div>
    """, unsafe_allow_html=True)

    # 予約内容カード
    selected_child = CHILD_OPTIONS[st.session_state.target_child_val]
    selected_time = TIME_OPTIONS[st.session_state.target_time_val]
    
    st.markdown(f"""
        <div class="info-card">
            <div style="text-align:center; font-weight:bold; color:#4CAF50; border-bottom:2px solid #eee; margin-bottom:10px; padding-bottom:5px;">
                📋 予約内容の確認
            </div>
            <div class="info-row">
                <span class="info-label">予約者</span>
                <span class="info-val">{selected_child.split(' ')[0]} {selected_child.split(' ')[1]}</span>
            </div>
            <div class="info-row">
                <span class="info-label">希望時間</span>
                <span class="info-val" style="color:#e91e63 !important; font-size:1.4rem;">{selected_time}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- ボタンエリア（横並び） ---
    # ここでボタンの色を強制的に分けます
    col_cancel, col_start = st.columns([1, 1])
    
    with col_cancel:
        # 訂正ボタン（白背景・グレー文字）
        st.markdown("""
            <style>
            div[data-testid="column"]:nth-of-type(1) div.stButton > button {
                background-color: #ffffff !important;
                color: #555555 !important;
                border: 2px solid #eeeeee !important;
            }
            </style>
        """, unsafe_allow_html=True)
        if st.button("訂正する"):
            st.session_state.step = 'input'
            st.rerun()

    with col_start:
        # 開始ボタン（ピンク背景・白文字）
        st.markdown("""
            <style>
            div[data-testid="column"]:nth-of-type(2) div.stButton > button {
                background-color: #f6adad !important;
                color: white !important;
                border: none !important;
            }
            </style>
        """, unsafe_allow_html=True)
        if st.button("🚀 待機開始"):
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

    # 黄色い警告（スリープ注意）
    st.markdown("""
        <div class="status-alert">
            ⚠️ 画面がスリープにならないように<br>設定してから寝てね！
        </div>
    """, unsafe_allow_html=True)

    status_placeholder = st.empty()

    # 時間計算
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.datetime.now(jst)
    target_dt = now.replace(hour=6, minute=0, second=0, microsecond=0)
    if now.hour >= 6:
        target_dt += datetime.timedelta(days=1)
    login_start_dt = target_dt - datetime.timedelta(minutes=10)

    # 待機中ステータス
    status_placeholder.markdown(f"""
        <div class="status-green">
            <h2 style="margin:0; color:#2e7d32 !important; font-size:1.6rem;">💤 待機中...</h2>
            <div style="margin:15px 0; font-size:1.1rem;">
                <b>{login_start_dt.strftime('%H:%M')}</b> に先行ログイン
            </div>
            <div style="border-top:1px dashed #4CAF50; padding-top:10px; font-size:0.9rem; color:#555;">
                予約対象: {TARGET_NAME} 様 ({selected_time})
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 訂正・中止ボタン（白背景）
    st.write("")
    st.markdown("""
        <style>
        div.stButton > button {
            background-color: #ffffff !important;
            color: #777777 !important;
            border: 1px solid #cccccc !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if st.button("訂正・中止する"):
        st.session_state.step = 'input'
        st.rerun()
    st.caption("※ 反応しない場合はブラウザを再読み込みしてください")

    # --- 待機ループ ---
    while True:
        now = datetime.datetime.now(jst)
        wait_sec = (login_start_dt - now).total_seconds()
        if wait_sec <= 0: break
        time.sleep(1)

    # --- 先行ログイン処理 ---
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
