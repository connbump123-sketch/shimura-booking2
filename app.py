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
    page_title="しむら小児科 事前予約アプリ",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- デザイン調整 (CSS) ---
# サイトのイメージ（白背景、ピンクのボタン、緑のアクセント）に強制変換します
st.markdown("""
    <style>
    /* 1. 全体の背景を白、文字を濃いグレーに固定 */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
        color: #333333 !important;
    }
    
    /* 2. 全てのテキスト要素の視認性を確保 */
    h1, h2, h3, h4, h5, h6, p, div, span, label, li {
        color: #444444 !important;
        font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
    }
    
    /* 3. ラジオボタンとセレクトボックスのスタイル */
    /* 入力エリアの背景を白、枠線を薄いグレーに */
    div[data-baseweb="select"] > div, div[data-baseweb="base-input"] {
        background-color: #ffffff !important;
        border-color: #e0e0e0 !important;
        color: #333333 !important;
    }
    /* 選択肢の文字色 */
    div[data-baseweb="select"] span {
        color: #333333 !important;
    }
    /* ドロップダウンメニューの背景 */
    ul[role="listbox"], div[role="listbox"] {
        background-color: #ffffff !important;
    }
    
    /* 4. メインボタン（ピンク） */
    div.stButton > button {
        background-color: #f6adad !important; /* サイトのピンク色 */
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        padding: 0.6em 2em !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #ffb6b6 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }
    div.stButton > button:active {
        background-color: #e09090 !important;
        transform: translateY(0);
    }

    /* 5. ステータス表示エリア（緑のアクセント） */
    .status-box {
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        background-color: #f9fdf9; /* 極めて薄い緑 */
        border: 1px solid #d0e8d0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* 6. プログレスバーの色 */
    div[data-testid="stProgress"] > div > div {
        background-color: #f6adad !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏥 しむら小児科 事前予約アプリ")
st.caption("【夜セット対応版】予約日の前日夜にセットし、スリープにならないように画面をつけたまま充電して寝てください。")

# --- 設定フォーム ---
st.subheader("1. 予約設定")

# コンテナを使ってレイアウトを整理
with st.container():
    # 子供選択
    target_child_str = st.radio(
        "予約するお子様",
        ["オオムラ イブキ 様 (12979)", "オオムラ エリナ 様 (10865)"],
        index=0
    )

    # 時間選択
    # 12時台の除外などロジックはそのまま
    target_time_str = st.selectbox(
        "希望開始時間",
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

# --- 実行ボタンエリア ---
st.markdown("---")
st.subheader("2. 実行")

if st.button("🌙 おやすみ前セット（待機開始）", type="primary"):
    
    # ログ表示エリアの作成（独自のスタイル適用）
    status_placeholder = st.empty()
    log_container = st.container()
    
    # 時間計算
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.datetime.now(jst)
    target_dt = now.replace(hour=6, minute=0, second=0, microsecond=0)
    if now.hour >= 6:
        target_dt += datetime.timedelta(days=1)
    
    # 先行ログイン開始時間（10分前）
    login_start_dt = target_dt - datetime.timedelta(minutes=10)
    
    # --- Phase 1: 待機 (ロングスリープ) ---
    # 分かりやすいデザインで表示
    status_placeholder.markdown(f"""
        <div class="status-box">
            <h3 style="margin-top:0;">✅ セット完了！</h3>
            <p><b>{login_start_dt.strftime('%H:%M')}</b> にブラウザを起動し、先行ログインします。</p>
            <p style="color: #e64a19 !important;">⚠️ 重要: スマホの自動ロックを解除し、画面を点灯させたままにしてください。</p>
        </div>
    """, unsafe_allow_html=True)
    
    while True:
        now = datetime.datetime.now(jst)
        wait_sec = (login_start_dt - now).total_seconds()
        
        if wait_sec <= 0:
            break
            
        # 残り時間の更新（シンプルに）
        if wait_sec > 60:
            # 負荷軽減のため10秒おき更新
            time.sleep(10)
        else:
            time.sleep(1)

    # --- Phase 2: 先行ログイン & 待機 ---
    status_placeholder.markdown("""
        <div class="status-box">
            <h3>🚀 先行ログインを実行中...</h3>
            <p>Cookieを取得し、スタートダッシュの準備をしています。</p>
        </div>
    """, unsafe_allow_html=True)
    
    driver = None
    try:
        driver = get_driver()
        wait = WebDriverWait(driver, 20)
        
        # サイトアクセス & ログイン
        driver.get(START_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # 子供選択
        try:
            # ラベルをクリック
            driver.find_element(By.XPATH, f"//label[contains(., '{TARGET_ID}')]").click()
            # ログインボタンをクリック
            driver.find_element(By.XPATH, "//button[contains(., 'ログイン')]").click()
            st.toast(f"✅ {TARGET_NAME}様で先行ログイン成功")
        except:
            st.warning("ログイン画面をスキップしました（既にログイン済みの可能性があります）")

        # 待機ループ
        while True:
            now = datetime.datetime.now(jst)
            remaining = (target_dt - now).total_seconds()
            
            if remaining <= 10:
                break
            
            status_placeholder.markdown(f"""
                <div class="status-box">
                    <h3>🕒 6:00 開門待ち...</h3>
                    <p>あと <b>{int(remaining)}</b> 秒</p>
                    <p>ログイン状態を維持しています。</p>
                </div>
            """, unsafe_allow_html=True)
            
            # セッション維持
            _ = driver.current_url 
            time.sleep(1)

        # --- Phase 3: ロケットダッシュ ---
        status_placeholder.markdown("""
            <div class="status-box" style="border-color: #f6adad; background-color: #fff0f0;">
                <h3 style="color: #d32f2f !important;">🔥 ロケットダッシュ開始！</h3>
                <p>予約ボタンを連打しています...</p>
            </div>
        """, unsafe_allow_html=True)
        
        # ボタン連打ループ
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
            
            # タイムアウト
            if (datetime.datetime.now(jst) - target_dt).total_seconds() > 60:
                raise Exception("予約ボタンが出現しませんでした。")

        # --- Phase 4: 予約ステップ ---
        # 1. 時間帯選択
        st.write(f"🔍 {TARGET_H_JP}代を選択...")
        time_band_xpath = f"//td[contains(., '{TARGET_H_JP}')]/following-sibling::td/a[contains(., '〇') or contains(., '△')]"
        wait.until(EC.element_to_be_clickable((By.XPATH, time_band_xpath))).click()
        
        # 2. 詳細時間選択
        st.write(f"🔍 {TARGET_M_JP}を選択...")
        detail_time_xpath = f"//td[contains(., '{TARGET_M_JP}')]/following-sibling::td/a[contains(., '〇') or contains(., '△')]"
        wait.until(EC.element_to_be_clickable((By.XPATH, detail_time_xpath))).click()
        
        # 3. 確認画面へ
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '確認') or contains(., '次へ') or @type='submit']")))
        driver.execute_script("arguments[0].scrollIntoView();", next_btn)
        next_btn.click()
        
        # 4. 最終確定
        st.write("🔥 最終確定！")
        final_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '予 約')]")))
        
        # ★本番実行（本番前に次の行の#を外し有効化する）★
        # final_btn.click()
        
        # 成功表示
        st.balloons()
        status_placeholder.markdown("""
            <div class="status-box" style="border-color: #4CAF50; background-color: #e8f5e9;">
                <h3 style="color: #2e7d32 !important;">🏆 予約完了しました！</h3>
                <p>完了画面を確認してください。</p>
            </div>
        """, unsafe_allow_html=True)
        
        time.sleep(2)
        st.image(driver.get_screenshot_as_png(), caption="結果画面")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        if driver:
            st.image(driver.get_screenshot_as_png(), caption="エラー時の画面")
    finally:
        if driver:
            driver.quit()
