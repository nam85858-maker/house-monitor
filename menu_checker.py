import os
import requests
from bs4 import BeautifulSoup
import hashlib
import asyncio
from telegram import Bot

# --- [GitHub Secrets 설정] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# 알려주신 카카오톡 채널 특정 포스트 주소
URL = "https://pf.kakao.com/_TkQxhG/113009898"
HISTORY_FILE = "last_menu_hash.txt"

async def send_telegram(description):
    bot = Bot(token=TELEGRAM_TOKEN)
    message = f"🍱 [식단표 업데이트 알림]\n\n식단 내용이 변경되었습니다!\n\n바로가기: {URL}\n\n[미리보기]\n{description}"
    print("🚀 텔레그램 전송 시작")
    await bot.send_message(chat_id=CHAT_ID, text=message)

def run_check():
    print("🌐 식단 채널 접속 중...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(URL, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 카카오 채널은 미리보기 메타 태그(og:image, og:description)에 핵심 내용이 들어있습니다.
        desc_meta = soup.find('meta', property='og:description')
        img_meta = soup.find('meta', property='og:image')

        description = desc_meta['content'] if desc_meta else "내용 없음"
        image_url = img_meta['content'] if img_meta else ""

        # 텍스트와 이미지 주소를 합쳐서 고유한 '지문(Hash)'을 만듭니다.
        # 점 하나만 바뀌거나 식단표 이미지가 교체되어도 지문이 완전히 바뀝니다.
        current_data = description + image_url
        current_hash = hashlib.md5(current_data.encode('utf-8')).hexdigest()

        # 기존 지문 읽기
        last_hash = ""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                last_hash = f.read().strip()

        print(f"📂 이전 식단 지문: {last_hash}")
        print(f"🔍 현재 식단 지문: {current_hash}")

        # 지문이 다르면 = 식단이 바뀌었다면
        if current_hash != last_hash:
            print("🎯 식단 변경 감지! 텔레그램을 전송합니다.")
            if TELEGRAM_TOKEN and CHAT_ID:
                asyncio.run(send_telegram(description))

            # 새 지문 저장
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                f.write(current_hash)
            print("💾 최신 식단 기록 완료.")
        else:
            print("📭 식단 내용이 아직 그대로입니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    run_check()
