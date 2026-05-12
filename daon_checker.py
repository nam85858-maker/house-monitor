import os
import time
import hashlib
import asyncio
import requests
from telegram import Bot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# 🔥 여기에 다온푸드 카카오 채널 홈 주소를 넣어주세요! (posts 빼고 홈 주소)
# 예시: "https://pf.kakao.com/_xxxxxx"
CHANNEL_URL = "여기에_다온푸드_주소를_붙여넣으세요"
HISTORY_FILE = "last_daon_hash.txt"

async def send_telegram_photo(img_data):
    bot = Bot(token=TELEGRAM_TOKEN)
    caption = "🍱 [다온푸드] 오늘의 식단표(프로필 사진)가 업데이트되었습니다!"
    print("🚀 텔레그램 전송 시도 중...")
    
    try:
        # 다운받은 이미지를 텔레그램으로 전송
        await bot.send_photo(chat_id=CHAT_ID, photo=img_data, caption=caption)
        print("✅ 프로필 사진 전송 성공!")
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")

def run_check():
    if CHANNEL_URL == "여기에_다온푸드_주소를_붙여넣으세요":
        print("❌ CHANNEL_URL이 설정되지 않았습니다. 코드를 수정해주세요.")
        return

    print("🌐 다온푸드 채널 접속 중...")
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # 게시글 목록(/posts)이 아닌 채널 메인 홈으로 접속합니다.
        driver.get(CHANNEL_URL)
        print("⏳ 로딩 대기 중 (7초)...")
        time.sleep(7)

        # 프로필 사진 원본(고화질) 주소 가져오기
        try:
            img_meta = driver.find_element(By.XPATH, '//meta[@property="og:image"]')
            img_url = img_meta.get_attribute("content")
        except Exception as e:
            print("❌ 프로필 사진을 찾을 수 없습니다.")
            return

        # 이미지 다운로드 및 해시(지문) 생성
        img_data = requests.get(img_url).content
        current_hash = hashlib.md5(img_data).hexdigest()

        # 기존 지문 읽기
        last_hash = ""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                last_hash = f.read().strip()

        if current_hash != last_hash:
            print("🎯 프로필 사진 변경 감지! 텔레그램을 전송합니다.")
            if TELEGRAM_TOKEN and CHAT_ID:
                asyncio.run(send_telegram_photo(img_data))

            # 새 지문 저장
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                f.write(current_hash)
            print("💾 최신 프로필 기록 완료.")
        else:
            print("📭 프로필 사진이 아직 그대로입니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_check()
