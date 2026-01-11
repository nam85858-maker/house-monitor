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
import hashlib # 사진의 지문을 만들기 위한 도구
from PIL import Image
from io import BytesIO

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
HISTORY_FILE = 'last_image_hash.txt' # 주소 대신 해시값(지문) 저장

async def send_telegram(photo_bytes):
    bot = Bot(token=TELEGRAM_TOKEN)
    img = Image.open(BytesIO(photo_bytes))
    rotated_img = img.rotate(90, expand=True) # 90도 또는 270도로 조절
    
    temp_photo = "rotated_house.jpg"
    rotated_img.save(temp_photo)
    
    await bot.send_message(chat_id=CHAT_ID, text="🏠 집 상태 사진이 업데이트되었습니다!")
    with open(temp_photo, 'rb') as photo:
        await bot.send_photo(chat_id=CHAT_ID, photo=photo)
    
    if os.path.exists(temp_photo):
        os.remove(temp_photo)

def run_check():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://pf.kakao.com/_sixfwG/posts") 
        time.sleep(7) # 카카오는 로딩이 길 수 있어 7초로 늘림

        xpath = '//*[@id="mArticle"]/div[2]/div[1]/div[2]/div/img'
        img_element = driver.find_element(By.XPATH, xpath)
        current_img_url = img_element.get_attribute('src')

        # 1. 사진 데이터를 직접 다운로드
        response = requests.get(current_img_url)
        img_data = response.content
        
        # 2. 사진의 '지문(Hash)' 생성
        current_hash = hashlib.md5(img_data).hexdigest()

        # 3. 이전 지문과 비교
        last_hash = ""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                last_hash = f.read().strip()

        if current_hash != last_hash:
            print("사진 내용 변경 감지! 전송 중...")
            asyncio.run(send_telegram(img_data))
            with open(HISTORY_FILE, 'w') as f:
                f.write(current_hash)
        else:
            print("사진 내용이 이전과 동일합니다.")

    except Exception as e:
        print(f"오류: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_check()
