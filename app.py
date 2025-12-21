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
st.set_page_config(page_title="しむら小児科予約", page_icon="🏥")

st.title("🏥 しむら小児科 予約アプリ")
st.caption("Developed by Gemini for Omura Family")

# --- サイドバー設定（デバッグ用） ---
with st.sidebar:
    st.write("システムステータス")
    screenshot_placeholder = st.empty()

# --- ユーザー入力フォーム ---
st.subheader("1. 予約設定")
col1, col2 = st.columns(2)

with col1:
    # 子供の選択
    child_choice = st.radio(
        "誰の予約？",
        ["イブキ (12979)", "エリナ (10865)"],
        index=0
    )

with col2:
    # 時間の選択（ここをクロックウィジェット方式に変更！）
    # デフォルトを9:00に設定、15分刻み(900秒)
    input_time = st.time_input(
        "希望時間",
        value=datetime.time(9, 0),
        step=900 
    )
    # プログラム用に "09:00" のような文字列に変換
    time_choice = input_time.strftime("%H:%M")

# ターゲット設定
TARGET_ID = "12979" if "イブキ" in child_choice else "10865"
TARGET_NAME = "イブキ" if "イブキ" in child_choice else "エリナ"
TARGET_URL = "https://shimura-kids.com/yoyaku/php/line_login.php"

# --- ブラウザ起動関数 ---
def get_driver():
    options = Options()
    options.add_argument('--headless') 
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1')
    return webdriver.Chrome(options=options)

# --- 実行ボタン ---
if st.button("🚀 予約待機モード開始", type="primary"):
    
    st.write("---")
    status_log = st.empty()
    image_log = st.empty()

    # 1. 時間管理（6:00まで待機）
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.datetime.now(jst)
    target_dt = now.replace(hour=6, minute=0, second=0, microsecond=0)
    
    if now.hour >= 6:
        # 6時過ぎなら翌日の6時に設定（ただし今はテストのため即時実行に流すことも可能）
        if now.hour < 18: # 診療時間内なら即時実行とみなす
             status_log.warning(f"⚠️ 現在6時を過ぎています。指定時刻 {time_choice} の枠を狙って即時実行します。")
        else:
             target_dt += datetime.timedelta(days=1)
             status_log.info(f"🌙 明日の朝6:00に向けて待機します...")

    # 待機ロジック（6時前の場合のみ発動）
    if now.hour < 6:
        wait_seconds = (target_dt - now).total_seconds()
        status_log.info(f"⏰ 朝6:00まであと {wait_seconds/60:.1f} 分待機します。画面を閉じないでください...")
        
        if wait_seconds > 60:
            time.sleep(wait_seconds - 60)
            wait_seconds = 60
        
        progress_bar = st.progress(0)
        for i in range(int(wait_seconds), 0, -1):
            status_log.info(f"🔥 突撃まであと {i} 秒！")
            progress_bar.progress((60-i)/60)
            time.sleep(1)
        progress_bar.empty()

    # --- Selenium実行開始 ---
    status_log.success(f"🚀 ブラウザ起動中... {time_choice} の枠を狙います！")
    
    driver = None
    try:
        driver = get_driver()
        wait = WebDriverWait(driver, 10)
        
        # 1. サイトへアクセス
        driver.get(TARGET_URL)
        image_log.image(driver.get_screenshot_as_png(), caption="現在の画面")

        # 2. 子供選択
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        try:
            target_xpath = f"//*[contains(text(), '{TARGET_ID}')]"
            driver.find_element(By.XPATH, target_xpath).click()
            status_log.info(f"✅ {TARGET_NAME}さんを選択")
            
            login_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'ログイン') or contains(@class, 'btn')]")
            login_btn.click()
            status_log.info("✅ ログインボタン押下")
            time.sleep(2)
        except Exception as e:
            status_log.warning("⚠️ 選択画面スキップ（既にログイン済み等の可能性）")

        image_log.image(driver.get_screenshot_as_png(), caption="ログイン後の画面")

        # 3. 受付開始待ちループ
        max_retries = 10
        for i in range(max_retries):
            if "予約受付を行っておりません" in driver.page_source:
                status_log.warning(f"⏳ 受付開始前...リロードします ({i+1}/{max_retries})")
                driver.refresh()
                time.sleep(1)
            else:
                status_log.success("🎉 受付画面を検知！")
                break
        
        # 4. 予約時間のクリック（Clock Widgetで選んだ時間を使う）
        try:
            # 画面上のボタンテキストと一致するか検索
            # 例: "09:00" や "9:00" など表記揺れに対応するため、ゼロ埋めなしも試す
            time_str_simple = f"{input_time.hour}:{input_time.minute:02}" # 9:00
            
            # 検索パターン（09:00 または 9:00）
            time_xpath = f"//*[contains(text(), '{time_choice}') or contains(text(), '{time_str_simple}')]"
            
            time_btn = wait.until(EC.element_to_be_clickable((By.XPATH, time_xpath)))
            driver.execute_script("arguments[0].scrollIntoView();", time_btn)
            time_btn.click()
            status_log.success(f"✅ {time_choice} のボタンをクリックしました！")
            
            time.sleep(2)
            image_log.image(driver.get_screenshot_as_png(), caption="結果画面")
            st.balloons()
            st.success("処理完了！画像で結果を確認してください。")

        except Exception as e:
            status_log.error(f"❌ 指定された時間 {time_choice} の枠が見つかりませんでした。満枠か、休診の可能性があります。")
            image_log.image(driver.get_screenshot_as_png(), caption="エラー時の画面")

    except Exception as e:
        st.error(f"システムエラー: {e}")
    finally:
        if driver:
            driver.quit()
