import asyncio
from telegram import Bot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import os
import time

# GitHub Secrets에서 정보를 가져옵니다
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

async def send_telegram(photo_url):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text="🏠 사진 변경 감지! 확인해 보세요.")
    await bot.send_photo(chat_id=CHAT_ID, photo=photo_url)

def run_check():
    chrome_options = Options()
    chrome_options.add_argument('--headless') # 서버에선 창을 띄울 수 없으므로 필수
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # 확인하고 싶은 웹사이트 주소를 여기에 넣으세요
        driver.get("https://pf.kakao.com/_sixfwG/112042925") 
        time.sleep(5)

        xpath = '//*[@id="mArticle"]/div[2]/div[1]/div[2]/div/img'
        img_element = driver.find_element(By.XPATH, xpath)
        img_url = img_element.get_attribute('src')
        
        # 서버 실행이므로 매번 사진을 보내도록 설정 (또는 변경 감지 로직 추가 가능)
        asyncio.run(send_telegram(img_url))
        print("전송 성공")

    except Exception as e:
        print(f"오류: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_check()