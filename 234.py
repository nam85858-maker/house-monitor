import asyncio
from telegram import Bot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import os
import time
import requests
import hashlib
from PIL import Image
from io import BytesIO

# --- [보안 처리: GitHub Secrets에서 값을 가져옵니다] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
# ---------------------------------------------------

HISTORY_FILE = 'last_image_hash.txt'

async def send_telegram(photo_bytes):
    bot = Bot(token=TELEGRAM_TOKEN)
    img = Image.open(BytesIO(photo_bytes))
    
    # [회전 수정] 270도에서 90도로 변경 (거꾸로 나오면 90이 정답입니다)
    rotated_img = img.rotate(90, expand=True) 
    
    temp_photo = "rotated_menu.jpg"
    rotated_img.save(temp_photo, quality=95)
    
    print("텔레그램 전송 중...")
    await bot.send_message(chat_id=CHAT_ID, text="🍱 이번 주 식단표가 도착했습니다!")
    with open(temp_photo, 'rb') as photo:
        await bot.send_photo(chat_id=CHAT_ID, photo=photo)
    if os.path.exists(temp_photo):
        os.remove(temp_photo)

def run_check():
    chrome_options = Options()
    chrome_options.add_argument('--headless') # GitHub에서는 무조건 headless 모드여야 합니다.
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        print("1. 카카오 채널 접속 중...")
        driver.get("https://pf.kakao.com/_sixfwG/posts")
        time.sleep(7)

        # 게시글 상세 주소 찾기
        links = driver.find_elements(By.TAG_NAME, "a")
        detail_url = None
        for link in links:
            href = link.get_attribute('href')
            if href and "/_sixfwG/" in href and any(char.isdigit() for char in href):
                detail_url = href
                break
        
        if not detail_url:
            print("게시글 주소를 찾지 못했습니다.")
            return

        # 2. 상세 페이지 이동
        driver.get(detail_url)
        time.sleep(5)

        # 3. 사진 주소 추출 및 변경 확인
        img_url = driver.find_element(By.XPATH, '//meta[@property="og:image"]').get_attribute('content')
        response = requests.get(img_url)
        img_data = response.content
        current_hash = hashlib.md5(img_data).hexdigest()

        # 이전 기록 비교
        last_hash = ""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                last_hash = f.read().strip()

        if current_hash != last_hash:
            print("새로운 메뉴판 감지! 전송합니다.")
            asyncio.run(send_telegram(img_data))
            with open(HISTORY_FILE, 'w') as f:
                f.write(current_hash)
        else:
            print("이미 전송된 메뉴판입니다.")

    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_check()
