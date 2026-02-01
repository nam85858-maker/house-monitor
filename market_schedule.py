import os
import time
import requests
import asyncio
import hashlib
from telegram import Bot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- [설정] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
SCHEDULE_HISTORY = 'last_market_schedule.txt'

async def send_telegram(msg):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=msg)

def run_check():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://www.fsale.kr/page.php?pgid=about")
        
        # 1. '전통시장' 글자가 나타날 때까지 최대 15초 기다립니다.
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '전통시장')]")))
        
        # 2. 페이지 전체 텍스트를 가져와서 '전통시장' 이후 내용만 추출합니다.
        full_text = driver.find_element(By.TAG_NAME, "body").text
        if "전통시장" in full_text:
            # '전통시장' 단어 뒤의 모든 텍스트를 데이터로 취급합니다.
            current_content = full_text.split("전통시장")[-1].strip()
        else:
            print("전통시장 키워드를 찾지 못했습니다.")
            return

        # 3. 변경 사항 확인
        current_hash = hashlib.md5(current_content.encode('utf-8')).hexdigest()
        
        last_hash = ""
        if os.path.exists(SCHEDULE_HISTORY):
            with open(SCHEDULE_HISTORY, 'r', encoding='utf-8') as f:
                last_hash = f.read().strip()

        if current_hash != last_hash:
            print("📅 전통시장 일정 변경 감지!")
            # 캡처하신 이미지의 일정 정보를 메시지에 포함
            message = "🚨 [수산대전] 전통시장 환급행사 일정이 업데이트되었습니다!\n\n"
            message += "설 온누리상품권 환급행사: 2.10(화) ~ 2.14(토)\n"
            message += "추석 온누리상품권 환급행사: 9.19(토) ~ 9.23(수)\n\n"
            message += "상세확인: https://www.fsale.kr/page.php?pgid=about"
            
            asyncio.run(send_telegram(message))
            
            with open(SCHEDULE_HISTORY, 'w', encoding='utf-8') as f:
                f.write(current_hash)
        else:
            print("변경 사항 없음 (알림 스킵)")

    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_check()
