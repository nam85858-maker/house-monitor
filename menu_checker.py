import os
import time
import hashlib
import asyncio
from telegram import Bot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# --- [GitHub Secrets 설정] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# 식당 채널의 메인 홈 주소 (특정 게시글이 아닌 전체 목록)
CHANNEL_URL = "https://pf.kakao.com/_TkQxhG"
HISTORY_FILE = "last_menu_hash.txt"

async def send_telegram_photo(image_url, description, post_url):
    bot = Bot(token=TELEGRAM_TOKEN)
    caption = f"🍱 [이번 주 식단표 업데이트]\n\n새로운 식단이 올라왔습니다!\n바로가기: {post_url}"
    print("🚀 텔레그램 전송 시도 중...")
    
    try:
        if image_url:
            await bot.send_photo(chat_id=CHAT_ID, photo=image_url, caption=caption)
            print("✅ 텔레그램 사진 전송 성공!")
        else:
            fallback_msg = f"{caption}\n\n[내용 미리보기]\n{description}"
            await bot.send_message(chat_id=CHAT_ID, text=fallback_msg)
            print("✅ 텍스트 전송 성공!")
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")

def run_check():
    print("🌐 식단 채널 접속 중...")
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # 1. 채널 메인 접속
        driver.get(CHANNEL_URL)
        time.sleep(5)

        # 2. 화면에 있는 모든 링크 중 '게시글(포스트)' 링크만 찾기
        links = driver.find_elements(By.TAG_NAME, "a")
        latest_post_url = None

        for link in links:
            href = link.get_attribute("href")
            # 카카오 포스트 주소 형식에 맞고, 맨 뒤가 숫자(게시글 번호)인 것 찾기
            if href and "/_TkQxhG/" in href:
                post_id = href.split("/")[-1]
                if post_id.isdigit(): 
                    latest_post_url = href
                    break # 첫 번째로 찾은 게 가장 최신 글!

        if not latest_post_url:
            print("❌ 최신 게시글 링크를 찾을 수 없습니다.")
            return

        print(f"🔗 최신 게시글 자동 발견: {latest_post_url}")

        # 3. 발견한 최신 게시글로 직접 이동
        driver.get(latest_post_url)
        time.sleep(3)

        # 이미지와 내용 추출
        try:
            img_meta = driver.find_element(By.XPATH, "//meta[@property='og:image']")
            image_url = img_meta.get_attribute("content")
        except:
            image_url = ""

        try:
            desc_meta = driver.find_element(By.XPATH, "//meta[@property='og:description']")
            description = desc_meta.get_attribute("content")
        except:
            description = "내용 없음"

        # 4. 해시(지문) 생성 및 비교
        # 주소나 이미지가 하나라도 바뀌면 지문이 변경됨
        current_data = latest_post_url + image_url
        current_hash = hashlib.md5(current_data.encode('utf-8')).hexdigest()

        last_hash = ""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                last_hash = f.read().strip()

        print(f"📂 이전 지문: {last_hash}")
        print(f"🔍 현재 지문: {current_hash}")

        if current_hash != last_hash:
            print("🎯 새로운 식단표 감지! 텔레그램을 전송합니다.")
            if TELEGRAM_TOKEN and CHAT_ID:
                asyncio.run(send_telegram_photo(image_url, description, latest_post_url))

            # 새 지문 저장
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                f.write(current_hash)
            print("💾 최신 식단 기록 완료.")
        else:
            print("📭 아직 새로운 식단이 올라오지 않았습니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_check()
