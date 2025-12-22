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
    page_icon="🐼",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS (デザイン調整) ---
st.markdown("""
<style>
    /* 全体の背景と文字色を明るく */
    .stApp {
        background-color: #ffffff;
        color: #C0C0C0;
    }
    /* ボタンの色をサイトの緑/ピンクに合わせる */
    div.stButton > button:first-child {
        background-color: #f6adad; /* ピンク */
        color: #C0C0C0;
        border: none;
        border-radius: 5px;
        font-weight: bold;
    }
    div.stButton > button:active {
        background-color: #e09090;
    }
    /* ヘッダーの色 */
    h1, h2, h3 {
        color: #4CAF50; /* 緑 */
    }
    /* ラジオボタンのアクセント */
    div[role="radiogroup"] > label > div:first-child {
        background-color: #4CAF50 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏥 しむら小児科 予約エージェント")
st.caption("【夜セット対応版】前日の夜にセットし、画面をつけたまま充電して寝てください。")

# --- 設定フォーム ---
st.subheader("1. 予約設定")
target_child_str = st.radio("予約するお子様", ["オオムラ イブキ 様 (12979)", "オオムラ エリナ 様 (10865)"], index=0)

# 時間選択（除外ロジック込み）
target_time_str = st.selectbox(
    "希望開始時間",
    [f"{h:02d}:{m:02d}" for h in range(9, 18) for m in [0, 15, 30, 45] 
     if not (h == 12 and m > 0) and not (h > 12 and h < 15) and not (h == 17 and m > 30)],
    index=0
)

# 設定値
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

# --- 実行ボタン ---
st.markdown("---")
if st.button("🌙 おやすみ前セット（待機開始）", type="primary"):
    
    log_container = st.container()
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # 時間計算
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.datetime.now(jst)
    target_dt = now.replace(hour=6, minute=0, second=0, microsecond=0)
    if now.hour >= 6:
        target_dt += datetime.timedelta(days=1)
    
    # ログイン開始時間（10分前）
    login_start_dt = target_dt - datetime.timedelta(minutes=10)
    
    # --- Phase 1: 朝5:50まで待機 (ロングスリープ) ---
    with log_container:
        st.info(f"✅ セット完了！ {login_start_dt.strftime('%H:%M')} にブラウザを起動し、先行ログインします。")
        st.warning("⚠️ 重要: スマホの自動ロックを解除し、画面を点灯させたままにしてください。")
    
    while True:
        now = datetime.datetime.now(jst)
        wait_sec = (login_start_dt - now).total_seconds()
        
        if wait_sec <= 0:
            break
            
        # 表示更新（1分毎）
        hours = int(wait_sec // 3600)
        mins = int((wait_sec % 3600) // 60)
        status_text.markdown(f"### 💤 待機中... 先行ログインまで あと {hours}時間 {mins}分")
        
        # Keep-Alive対策（小刻みにsleep）
        sleep_chunk = 10 if wait_sec > 60 else 1
        time.sleep(sleep_chunk)

    # --- Phase 2: 先行ログイン & 待機 (5:50〜5:59) ---
    status_text.markdown("### 🚀 ブラウザ起動 & 先行ログイン開始！")
    driver = None
    try:
        driver = get_driver()
        wait = WebDriverWait(driver, 20)
        
        # サイトアクセス & ログイン
        driver.get(START_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # 子供選択
        try:
            driver.find_element(By.XPATH, f"//label[contains(., '{TARGET_ID}')]").click()
            driver.find_element(By.XPATH, "//button[contains(., 'ログイン')]").click()
            st.toast(f"✅ {TARGET_NAME}様で先行ログイン成功")
        except:
            st.error("ログイン画面が見つかりません。既にログイン済みの可能性があります。")

        # 待機ループ (6:00突入直前まで)
        st.info("🕒 ログイン状態をキープして、6:00の開門を待ちます...")
        
        while True:
            now = datetime.datetime.now(jst)
            remaining = (target_dt - now).total_seconds()
            
            # 突入10秒前になったらループを抜ける
            if remaining <= 10:
                break
            
            status_text.markdown(f"### ⏳ 開門まであと {int(remaining)} 秒")
            
            # セッション維持のため、時々現在のURLを取得するだけの操作を行う
            _ = driver.current_url 
            time.sleep(1)

        # --- Phase 3: ロケットダッシュ (5:59:50〜) ---
        status_text.markdown("### 🔥 ロケットダッシュ開始！連打モード！！")
        
        # リトライループ（予約ボタンが出るまで更新または押下）
        start_dash_time = time.time()
        while True:
            try:
                # 「予約」ボタンを探す
                btns = driver.find_elements(By.XPATH, "//button[contains(., '予 約') or contains(., '予約')]")
                if btns:
                    btns[0].click()
                    st.success("🎉 予約ボタン押し込み成功！")
                    break
                else:
                    # ボタンがない＝まだ時間外、リロードして再試行
                    driver.refresh()
                    # 少しだけ待つ（負荷対策）
                    time.sleep(0.5)
            except:
                driver.refresh()
            
            # 6:01を過ぎてもダメならエラー
            if (datetime.datetime.now(jst) - target_dt).total_seconds() > 60:
                raise Exception("予約ボタンが出現しませんでした。")

        # --- Phase 4: 以降の予約ステップ (既存ロジック) ---
        
        # 時間帯選択
        st.write(f"🔍 {TARGET_H_JP}代を選択中...")
        time_band_xpath = f"//td[contains(., '{TARGET_H_JP}')]/following-sibling::td/a[contains(., '〇') or contains(., '△')]"
        wait.until(EC.element_to_be_clickable((By.XPATH, time_band_xpath))).click()
        
        # 詳細時間選択
        st.write(f"🔍 {TARGET_M_JP}を選択中...")
        detail_time_xpath = f"//td[contains(., '{TARGET_M_JP}')]/following-sibling::td/a[contains(., '〇') or contains(., '△')]"
        wait.until(EC.element_to_be_clickable((By.XPATH, detail_time_xpath))).click()
        
        # 確認画面へ
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '確認') or contains(., '次へ') or @type='submit']")))
        driver.execute_script("arguments[0].scrollIntoView();", next_btn)
        next_btn.click()
        
        # 最終確定
        st.write("🔥 最終確定ボタンを押します！")
        final_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '予 約')]")))
        
        # 本番では次の行のコメントアウトを外す！
        # final_btn.click()
        
        st.balloons()
        st.success("🏆 予約完了！（シミュレーション完了）")
        time.sleep(2)
        st.image(driver.get_screenshot_as_png(), caption="予約完了画面（想定）")

    except Exception as e:
        st.error(f"エラー: {e}")
        if driver:
            st.image(driver.get_screenshot_as_png(), caption="エラー時の画面")
    finally:
        if driver:
            driver.quit()
