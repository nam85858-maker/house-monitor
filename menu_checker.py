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

# 식당 채널의 '소식(Posts)' 탭 주소로 다이렉트 접속
CHANNEL_URL = "https://pf.kakao.com/_TkQxhG/posts"
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
    # 카카오가 봇을 차단하지 않도록 PC 브라우저인 척 위장
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    # [핵심] 화면이 짤려서 글을 못 찾는 현상을 막기 위해 꽉 찬 FHD 해상도로 강제 고정
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # 1. 채널 '소식' 탭으로 직행
        driver.get(CHANNEL_URL)
        
        # [핵심] 깃허브 서버가 느리기 때문에 카카오 화면이 다 뜰 때까지 10초간 넉넉히 대기
        print("⏳ 카카오 페이지 로딩을 기다리는 중 (10초)...")
        time.sleep(10)
        
        # 숨겨진 글이 나타나도록 화면을 살짝 아래로 스크롤
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)

        # 2. 화면에 있는 링크 중 '게시글' 찾기
        links = driver.find_elements(By.TAG_NAME, "a")
        latest_post_url = None

        for link in links:
            href = link.get_attribute("href")
            if href and "/_TkQxhG/" in href:
                # 주소 맨 끝이 숫자로 끝나는지 확인 (예: /posts/1234567)
                parts = href.rstrip('/').split("/")
                post_id = parts[-1]
                if post_id.isdigit(): 
                    latest_post_url = href
                    break # 가장 먼저 발견된(최신) 글을 저장하고 멈춤

        if not latest_post_url:
            print("❌ 최신 게시글 링크를 찾을 수 없습니다. (카카오 로딩 지연 또는 주소 형식 다름)")
            return

        print(f"🔗 최신 게시글 발견: {latest_post_url}")

        # 3. 최신 게시글로 직접 이동
        driver.get(latest_post_url)
        print("⏳ 게시글 내용 읽는 중 (5초)...")
        time.sleep(5)

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
