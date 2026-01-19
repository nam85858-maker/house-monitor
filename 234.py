import asyncio
from telegram import Bot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import os, time, requests, hashlib
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta

# GitHub Secrets에서 정보 가져오기
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
HISTORY_FILE = 'last_image_hash.txt'
TIME_FILE = 'last_run_time.txt'

async def send_telegram(photo_bytes):
    bot = Bot(token=TELEGRAM_TOKEN)
    img = Image.open(BytesIO(photo_bytes))
    
    # [회전 수정] 180도 회전하여 뒤집힌 글자를 똑바로 세웁니다.
    rotated_img = img.rotate(180, expand=True) 
    
    temp_photo = "menu_final.jpg"
    rotated_img.save(temp_photo, quality=95)
    
    print("텔레그램 전송 중...")
    with open(temp_photo, 'rb') as photo:
        await bot.send_photo(chat_id=CHAT_ID, photo=photo, caption="🍱 이번 주 식단표를 똑바로 세워 가져왔습니다!")
    
    if os.path.exists(temp_photo):
        os.remove(temp_photo)

def run_check():
    # 실행 시간 기록 (한국 시간)
    kst_now = (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')
    with open(TIME_FILE, 'w', encoding='utf-8') as f:
        f.write(f"최종 실행 시간(KST): {kst_now}")

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://pf.kakao.com/_sixfwG/posts")
        time.sleep(7)

        links = driver.find_elements(By.TAG_NAME, "a")
        detail_url = next((l.get_attribute('href') for l in links if "/_sixfwG/" in str(l.get_attribute('href')) and any(c.isdigit() for c in str(l.get_attribute('href')))), None)
        
        if not detail_url: return

        driver.get(detail_url)
        time.sleep(5)

        img_url = driver.find_element(By.XPATH, '//meta[@property="og:image"]').get_attribute('content')
        img_data = requests.get(img_url).content
        curr_hash = hashlib.md5(img_data).hexdigest()

        # 중복 전송 방지
        last_hash = ""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                last_hash = f.read().strip()

        if curr_hash != last_hash:
            asyncio.run(send_telegram(img_data))
            with open(HISTORY_FILE, 'w') as f:
                f.write(curr_hash)
    finally:
        driver.quit()

if __name__ == "__main__":
    run_check()
