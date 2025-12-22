import streamlit as st
import time
import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# --- ページ設定（明るいテーマ、ピンクのアクセント） ---
st.set_page_config(
    page_title="しむら小児科予約エージェント",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# カスタムCSSで実際のサイトの雰囲気に近づける
st.markdown("""
    <style>
    /* 全体の背景と文字色を明るく */
    .stApp {
        background-color: #ffffff;
        color: #333333;
    }
    /* ボタンの色をサイトの緑/ピンクに合わせる */
    div.stButton > button:first-child {
        background-color: #f6adad; /* ピンク */
        color: white;
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
st.caption("ご希望の条件をセットしてください。朝6時に自動で予約を試みます。")

# --- ユーザー入力フォーム ---
st.subheader("1. 予約設定")

# 子供の選択
target_child_str = st.radio(
    "予約するお子様",
    ["オオムラ イブキ 様 (12979)", "オオムラ エリナ 様 (10865)"],
    index=0,
    help="診察券番号で識別します"
)

# 時間の選択（セレクトボックスに戻しました）
target_time_str = st.selectbox(
    "希望開始時間",
    [f"{h:02d}:{m:02d}" for h in range(9, 18) for m in [0, 15, 30, 45] if not (h == 12 and m > 0) and not (h > 12 and h < 15) and not (h == 17 and m > 30)],
    index=0,
    help="予約したい時間の「開始時間」を選んでください"
)

# --- 設定値の抽出 ---
TARGET_ID = "12979" if "12979" in target_child_str else "10865"
TARGET_NAME = "イブキ" if "イブキ" in target_child_str else "エリナ"
TARGET_H = target_time_str.split(':')[0] # "09"
TARGET_M = target_time_str.split(':')[1] # "00"
# サイトの表記に合わせる（例: "09時"→"9時", "00分"→"00分"）
TARGET_H_JP = f"{int(TARGET_H)}時"
TARGET_M_JP = f"{TARGET_H}時{TARGET_M}分"
START_URL = "https://shimura-kids.com/yoyaku/php/line_login.php"

# --- ブラウザ起動関数 ---
def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    # iPhoneとして偽装
    options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1')
    return webdriver.Chrome(options=options)

# --- メイン処理 ---
st.markdown("---")
st.subheader("2. 実行")

if st.button("🚀 予約待機モードを開始する", type="primary"):
    status_area = st.empty()
    log_area = st.container()
    
    with log_area:
        # 1. 時間管理（6:00まで待機）
        jst = pytz.timezone('Asia/Tokyo')
        now = datetime.datetime.now(jst)
        target_dt = now.replace(hour=6, minute=0, second=0, microsecond=0)
        
        if now.hour >= 6:
            # 6時過ぎなら翌日の6時に設定（テスト時はここをコメントアウトで即実行）
            # target_dt += datetime.timedelta(days=1) 
            st.warning("⚠️ 現在は受付時間内です。テストのため即時実行します。")
            wait_seconds = 0
        else:
            wait_seconds = (target_dt - now).total_seconds()
        
        if wait_seconds > 0:
            status_area.info(f"⏰ {target_dt.strftime('%m/%d %H:%M')} まで待機します。画面を閉じないでください。")
            # サーバー負荷対策：直前まで長めのスリープ
            if wait_seconds > 120:
                time.sleep(wait_seconds - 120)
                wait_seconds = 120
            
            # 直前カウントダウン
            progress_bar = st.progress(0)
            for i in range(int(wait_seconds), 0, -1):
                status_area.markdown(f"🔥 突撃まであと **{i}** 秒！")
                progress_bar.progress((wait_seconds - i) / wait_seconds)
                time.sleep(1)
            progress_bar.empty()

        status_area.success("🚀 予約プロセスを開始します！")
        
        driver = None
        try:
            driver = get_driver()
            wait = WebDriverWait(driver, 15)
            
            # --- Step 1: ログイン画面 ---
            st.write("🔄 サイトにアクセス中...")
            driver.get(START_URL)
            
            # 子供選択
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            # ラジオボタンのラベルを探してクリック
            target_label = driver.find_element(By.XPATH, f"//label[contains(., '{TARGET_ID}')]")
            target_label.click()
            st.write(f"✅ {TARGET_NAME}様を選択しました")
            
            # ログインボタンクリック
            login_btn = driver.find_element(By.XPATH, "//button[contains(., 'ログイン')]")
            login_btn.click()
            st.write("✅ ログインしました")
            time.sleep(3) # 遷移待ち
            
            # --- Step 2: メニュー画面 ---
            # ピンクの「予約」ボタンを探してクリック
            try:
                yoyaku_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '予 約') or contains(., '予約')]")))
                yoyaku_btn.click()
                st.write("✅ メニューから「予約」へ進みました")
                time.sleep(3)
            except:
                st.warning("⚠️ 「予約」ボタンが見つかりません。既に予約画面か、受付時間外の可能性があります。")

            # --- Step 3: 時間帯（〇時）選択画面 ---
            st.write(f"🔍 {TARGET_H_JP}代の空き枠を探しています...")
            # ロジック: 「9時」などのテキストがあるセルの、隣のセルにある「〇」リンクを探す
            # 例: //td[contains(text(), '9時')]/following-sibling::td/a[contains(text(), '〇')]
            try:
                time_band_xpath = f"//td[contains(., '{TARGET_H_JP}')]/following-sibling::td/a[contains(., '〇') or contains(., '△')]"
                time_band_link = wait.until(EC.element_to_be_clickable((By.XPATH, time_band_xpath)))
                time_band_link.click()
                st.write(f"✅ {TARGET_H_JP}代の枠を選択しました")
                time.sleep(3)
            except:
                raise Exception(f"{TARGET_H_JP}代に空き枠（〇または△）が見つかりませんでした。")

            # --- Step 4: 詳細時間（〇時〇分）選択画面 ---
            st.write(f"🔍 {TARGET_M_JP}の空き枠を探しています...")
            # ロジック: 「9時00分」などのテキストがあるセルの、隣のセルにある「〇」リンクを探す
            try:
                detail_time_xpath = f"//td[contains(., '{TARGET_M_JP}')]/following-sibling::td/a[contains(., '〇') or contains(., '△')]"
                detail_time_link = wait.until(EC.element_to_be_clickable((By.XPATH, detail_time_xpath)))
                detail_time_link.click()
                st.write(f"✅ {TARGET_M_JP}を選択しました")
                time.sleep(3)
            except:
                 raise Exception(f"{TARGET_M_JP}は既に埋まっているか、見つかりませんでした。")

            # --- Step 5: メール送信選択画面 ---
            st.write("🔄 最終確認へ進みます...")
            # 特に設定せず「次へ」のようなボタンを押す（画面下部にあると推測）
            # 汎用的な「進む」「確認」ボタン、またはフォーム送信ボタンを探す
            try:
                next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '確認') or contains(., '次へ') or @type='submit']")))
                # スクロールしてクリック
                driver.execute_script("arguments[0].scrollIntoView();", next_btn)
                next_btn.click()
                time.sleep(3)
            except:
                st.warning("⚠️ 「確認」へ進むボタンが見つかりませんでしたが、自動遷移した可能性があります。")

            # --- Step 6: 最終確認画面 ---
            st.write("🔥 最終確認画面です。「予約」ボタンを押します！")
            # ピンクの「予約」ボタンを探す
            try:
                final_submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '予 約')]")))
                # 本番では次の行のコメントアウトを外す！
                # final_submit_btn.click()
                st.success("🎉 予約ボタンをクリックしました！（シミュレーション完了）")
                
                # 完了後の画面をスクショ
                time.sleep(3)
                st.image(driver.get_screenshot_as_png(), caption="予約完了画面（想定）")

            except:
                 raise Exception("最終の「予約」ボタンが見つかりませんでした。")
            
            status_area.balloons()
            st.success("全ての処理が完了しました。予約メールが届いているか確認してください。")

        except Exception as e:
            status_area.error(f"❌ エラーが発生しました: {e}")
            if driver:
                st.image(driver.get_screenshot_as_png(), caption="エラー時の画面")
        finally:
            if driver:
                driver.quit()
