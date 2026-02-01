import feedparser
import asyncio
import os
import time
from datetime import datetime, timedelta
from telegram import Bot

# --- [GitHub Secrets 설정] ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# 제로페이 공식 블로그 RSS
RSS_URL = "https://rss.blog.naver.com/zeropay_official.xml"
HISTORY_FILE = "last_rss_link.txt"

async def send_telegram(title, link, date):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ 텔레그램 설정이 없습니다.")
        return
    
    bot = Bot(token=TELEGRAM_TOKEN)
    # 메시지 전송
    message = f"💳 [상품권 새 소식]\n\n제목: {title}\n날짜: {date}\n\n바로가기: {link}"
    print(f"🚀 전송 성공: {title}")
    await bot.send_message(chat_id=CHAT_ID, text=message)

def run_rss_check():
    print("📡 RSS 데이터 수신 중...")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("❌ RSS 데이터를 가져오지 못했습니다.")
        return

    # 1. 날짜 기준 설정 (오늘로부터 30일 전)
    # GitHub 서버 시간(UTC) 기준이지만, 30일 여유를 두므로 문제없습니다.
    limit_date = datetime.now() - timedelta(days=30)
    print(f"📅 날짜 필터 적용: {limit_date.strftime('%Y-%m-%d')} 이후 글만 확인합니다.")

    # 2. 기존 기록 읽기
    last_link = ""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            last_link = f.read().strip()
    
    print(f"📂 마지막 기록: {last_link if last_link else '없음 (최초 실행)'}")

    new_posts = []
    
    # 3. 글 목록 순회
    for entry in feed.entries:
        link = entry.link
        title = entry.title
        
        # 날짜 변환 (RSS 날짜 형식 -> 파이썬 날짜 객체)
        # published_parsed가 날짜 정보를 담고 있습니다.
        try:
            pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
        except:
            pub_date = datetime.now() # 날짜 에러 시 현재 시간으로 간주

        # [필터 1] 이미 확인한 글이면 중단
        if link == last_link:
            break
        
        # [필터 2] 30일이 지난 너무 오래된 글은 건너뛰기
        if pub_date < limit_date:
            continue

        # [필터 3] 키워드 검사 ([수산], [농할])
        if "[수산]" in title or "[농할]" in title:
            new_posts.append(entry)

    # 4. 전송 및 저장
    if new_posts:
        print(f"🎯 조건에 맞는 최신 글 {len(new_posts)}개 발견!")
        
        for entry in reversed(new_posts):
            # 보기 좋게 날짜 포맷팅 (YYYY-MM-DD)
            formatted_date = datetime.fromtimestamp(time.mktime(entry.published_parsed)).strftime('%Y-%m-%d')
            asyncio.run(send_telegram(entry.title, entry.link, formatted_date))
        
        # 가장 최신 글 링크 저장
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write(feed.entries[0].link)
        print("💾 최신 기록 업데이트 완료.")
        
    else:
        print("📭 최근 30일 내의 새로운 [수산]/[농할] 소식이 없습니다.")

if __name__ == "__main__":
    run_rss_check()
