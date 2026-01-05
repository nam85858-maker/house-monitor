import asyncio
from telegram import Bot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import os

# --- 설정 구간 ---
TELEGRAM_TOKEN = '8561709574:AAG4WWfgEEaswCbNDWLGwrM7YXb_1lxmZMs'
CHAT_ID = '862872708'
HISTORY_FILE = 'last_image.txt' # 마지막 사진 주소를 저장할 파일
# ----------------

async def send_telegram_msg(photo_url):
    bot = Bot(token=TELEGRAM_TOKEN)
    message = "🏠 확인 중인 웹사이트의 사진이 변경되었습니다!"
    await bot.send_message(chat_id=CHAT_ID, text=message)
    await bot.send_photo(chat_id=CHAT_ID, photo=photo_url)

def check_and_notify():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') # 알림용이므로 창 없이 실행
    driver = webdriver.Chrome(service=service, options=options)

    try:
        target_url = "https://pf.kakao.com/_sixfwG/112042925"
        driver.get(target_url)
        time.sleep(5)

        xpath = '//*[@id="mArticle"]/div[2]/div[1]/div[2]/div/img'
        img_element = driver.find_element(By.XPATH, xpath)
        current_img_url = img_element.get_attribute('src')

        # 이전에 저장된 이미지 주소 읽기
        last_img_url = ""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                last_img_url = f.read().strip()

        # 사진이 바뀌었는지 비교
        if current_img_url != last_img_url:
            print("새로운 사진 감지! 텔레그램 전송 중...")
            asyncio.run(send_telegram_msg(current_img_url))
            
            # 새로운 주소로 업데이트
            with open(HISTORY_FILE, 'w') as f:
                f.write(current_img_url)
        else:
            print("사진이 변경되지 않았습니다.")

    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    check_and_notify()