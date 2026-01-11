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
from PIL import Image # 이미지 회전을 위한 라이브러리
from io import BytesIO

# 설정 정보
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
HISTORY_FILE = 'last_image.txt'

async def send_telegram(photo_url):
    bot = Bot(token=TELEGRAM_TOKEN)
    
    # 1. 이미지 다운로드
    response = requests.get(photo_url)
    img = Image.open(BytesIO(response.content))
    
    # 2. 이미지 270도 회전 (시계 방향 기준 270도, 혹은 반시계 90도와 같음)
    rotated_img = img.rotate(90, expand=True)
    
    # 3. 회전된 이미지를 임시 파일로 저장
    temp_photo = "rotated_house.jpg"
    rotated_img.save(temp_photo)
    
    # 4. 메시지와 함께 회전된 사진 전송
    await bot.send_message(chat_id=CHAT_ID, text="🏠 사진 변경 감지! (270도 회전됨)")
    with open(temp_photo, 'rb') as photo:
        await bot.send_photo(chat_id=CHAT_ID, photo=photo)
    
    # 5. 사용한 임시 파일 삭제
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
        time.sleep(5)

        xpath = '//*[@id="mArticle"]/div[2]/div[1]/div[2]/div/img'
        img_element = driver.find_element(By.XPATH, xpath)
        current_img_url = img_element.get_attribute('src')

        last_img_url = ""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                last_img_url = f.read().strip()

        if current_img_url != last_img_url:
            print("새로운 사진 감지! 회전 후 전송 중...")
            asyncio.run(send_telegram(current_img_url))
            
            with open(HISTORY_FILE, 'w') as f:
                f.write(current_img_url)
        else:
            print("사진이 변경되지 않았습니다.")

    except Exception as e:
        print(f"오류: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_check()



