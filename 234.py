import asyncio
from telegram import Bot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import requests
import hashlib
from PIL import Image
from io import BytesIO

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
HISTORY_FILE = 'last_image_hash.txt'

async def send_telegram(photo_bytes):
    bot = Bot(token=TELEGRAM_TOKEN)
    img = Image.open(BytesIO(photo_bytes))
    # 사용자의 요청에 따라 회전 (90 또는 270 중 선택)
    rotated_img = img.rotate(90, expand=True) 
    
    temp_photo = "rotated_house.jpg"
    rotated_img.save(temp_photo, quality=95)
    
    await bot.send_message(chat_id=CHAT_ID, text="🏠 집 상태 사진이 감지되었습니다!")
    with open(temp_photo, 'rb') as photo:
        await bot.send_photo(chat_id=CHAT_ID, photo=photo)
    
    if os.path.exists(temp_photo):
        os.remove(temp_photo)

def run_check():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # 카카오 페이지가 로봇인걸 눈치채지 못하게 사용자 정보 흉내
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # 1. 주소 접속 (모바일 버전 주소가 더 안정적일 수 있음)
        driver.get("https://pf.kakao.com/_sixfwG/posts") 
        
        # 2. 사진이 나타날 때까지 최대 15초 대기
        wait = WebDriverWait(driver, 15)
        
        # 새로운 시도: 게시물 내의 이미지를 좀 더 포괄적으로 찾음
        # 기존 XPath가 실패할 경우를 대비해 여러 후보를 둡니다.
        img_url = None
        selectors = [
            '//*[@id="mArticle"]//div[@class="wrap_thumb"]//img',
            '//div[@class="thumb_img"]//img',
            '//*[@id="mArticle"]//img'
        ]
        
        for selector in selectors:
            try:
                element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                img_url = element.get_attribute('src')
                if img_url and 'http' in img_url:
                    break
            except:
                continue

        if not img_url:
            raise Exception("사진 위치를 찾을 수 없습니다. 페이지 구조가 변경되었을 수 있습니다.")

        # 3. 사진 데이터 다운로드 및 비교
        response = requests.get(img_url)
        img_data = response.content
        current_hash = hashlib.md5(img_data).hexdigest()

        last_hash = ""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                last_hash = f.read().strip()

        if current_hash != last_hash:
            print("변경 감지! 전송 시작...")
            asyncio.run(send_telegram(img_data))
            with open(HISTORY_FILE, 'w') as f:
                f.write(current_hash)
        else:
            print("변경 사항 없음.")

    except Exception as e:
        print(f"오류: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_check()
