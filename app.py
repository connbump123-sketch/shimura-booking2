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
    # 子供の選択（ラベルに含まれるテキストで判別します）
    child_choice = st.radio(
        "誰の予約？",
        ["イブキ (12979)", "エリナ (10865)"],
        index=0
    )

with col2:
    # 時間の選択
    time_choice = st.selectbox(
        "希望時間",
        ["09:00", "09:15", "09:30", "09:45",
         "10:00", "10:15", "10:30", "10:45",
         "11:00", "11:15", "11:30", "11:45",
         "15:30", "15:45", "16:00", "16:15",
         "16:30", "16:45", "17:00", "17:15", "17:30"],
        index=0
    )

# ターゲット設定
TARGET_ID = "12979" if "イブキ" in child_choice else "10865"
TARGET_NAME = "イブキ" if "イブキ" in child_choice else "エリナ"
TARGET_URL = "https://shimura-kids.com/yoyaku/php/line_login.php"

# --- ブラウザ起動関数 ---
def get_driver():
    options = Options()
    options.add_argument('--headless') # ヘッドレスモード
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    # iPhoneとして偽装（重要）
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
    target_time = now.replace(hour=6, minute=0, second=0, microsecond=0)
    
    # すでに6時を過ぎている場合は、テスト実行として即時動作させるか、翌日にするか
    if now.hour >= 6:
        status_log.warning("⚠️ 現在6時を過ぎています。即時実行モードで動きます（テスト用）")
        # テストのため待機なし
    else:
        # 待機ロジック
        wait_seconds = (target_time - now).total_seconds()
        status_log.info(f"⏰ 朝6:00まであと {wait_seconds/60:.1f} 分待機します。画面を閉じないでください...")
        
        # サーバー負荷軽減のため、直前までは長めのスリープ、1分前からカウントダウン
        if wait_seconds > 60:
            time.sleep(wait_seconds - 60)
            wait_seconds = 60
        
        # 直前カウントダウン
        progress_bar = st.progress(0)
        for i in range(int(wait_seconds), 0, -1):
            status_log.info(f"🔥 突撃まであと {i} 秒！")
            progress_bar.progress((60-i)/60)
            time.sleep(1)
        progress_bar.empty()

    # --- Selenium実行開始 ---
    status_log.success("🚀 ブラウザ起動中... 突撃します！")
    
    driver = None
    try:
        driver = get_driver()
        wait = WebDriverWait(driver, 10)
        
        # 1. サイトへアクセス
        driver.get(TARGET_URL)
        
        # 【重要】現在の画面を表示（LINEログインで止まってないか確認用）
        image_log.image(driver.get_screenshot_as_png(), caption="現在の画面")

        # 2. 子供選択画面の突破
        # ページ読み込み待ち
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        try:
            # ラジオボタンまたはラベルをクリック
            # 「12979」などのIDを含む要素を探してクリック
            target_xpath = f"//*[contains(text(), '{TARGET_ID}')]"
            target_element = driver.find_element(By.XPATH, target_xpath)
            target_element.click()
            status_log.info(f"✅ {TARGET_NAME}さんを選択しました")
            
            # ログインボタンクリック
            login_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'ログイン') or contains(@class, 'btn')]")
            login_btn.click()
            status_log.info("✅ ログインボタンを押下")
            time.sleep(2) # 遷移待ち
            
        except Exception as e:
            # 既にログイン済み、または画面が違う場合
            status_log.warning(f"⚠️ 選択画面をスキップ、またはエラー: {e}")

        # 最新画面を更新
        image_log.image(driver.get_screenshot_as_png(), caption="ログイン後の画面")

        # 3. 「時間外」か「予約可能」かの判定ループ
        # 6:00ジャストでも数秒ラグがあるため、リトライする
        max_retries = 10
        for i in range(max_retries):
            page_source = driver.page_source
            
            if "予約受付を行っておりません" in page_source:
                status_log.warning(f"⏳ まだ受付開始前です... リロードします ({i+1}/{max_retries})")
                driver.refresh()
                time.sleep(1) # 1秒待って再試行
            else:
                status_log.success("🎉 受付画面を検知しました！予約を試みます！")
                break
        
        # 4. 予約時間のクリック（予測ロジック）
        try:
            # 戦略: 「09:00」というテキストが含まれる、クリック可能な要素（ボタンやリンク）を探す
            # 汎用的なXPath: 何らかのタグの中に time_choice の文字列が含まれている
            time_xpath = f"//*[contains(text(), '{time_choice}')]"
            
            # 要素が見つかるまで待機
            time_btn = wait.until(EC.element_to_be_clickable((By.XPATH, time_xpath)))
            
            # スクロールしてクリック（隠れている場合対策）
            driver.execute_script("arguments[0].scrollIntoView();", time_btn)
            time_btn.click()
            status_log.success(f"✅ {time_choice} のボタンをクリックしました！")
            
            # 5. 最終確認（もしあれば）
            # 「確定」や「送信」ボタンがあれば押すロジックが必要だが、不明なため一旦ここでスクショ
            time.sleep(2)
            image_log.image(driver.get_screenshot_as_png(), caption="予約操作後の結果")
            
            status_log.balloons()
            st.success("処理が完了しました！上の画像で予約できているか確認してください。")

        except Exception as e:
            status_log.error(f"❌ 予約時間のボタンが見つかりませんでした...: {e}")
            image_log.image(driver.get_screenshot_as_png(), caption="エラー時の画面")

    except Exception as e:
        st.error(f"システムエラー: {e}")
    finally:
        if driver:
            driver.quit()
