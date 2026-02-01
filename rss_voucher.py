import feedparser
import asyncio
import os
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
    message = f"💳 [상품권 새 소식]\n\n제목: {title}\n\n바로가기: {link}"
    print(f"🚀 전송 성공: {title}")
    await bot.send_message(chat_id=CHAT_ID, text=message)

def run_rss_check():
    print("📡 RSS 데이터 수신 중...")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("❌ RSS 데이터를 가져오지 못했습니다.")
        return

    # 기존 기록 읽기
    last_link = ""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            last_link = f.read().strip()
    
    print(f"📂 마지막 기록: {last_link if last_link else '없음 (최초 실행)'}")

    new_posts = []
    
    # 최신 글부터 하나씩 검사
    for entry in feed.entries:
        link = entry.link
        title = entry.title
        
        if link == last_link:
            break
            
        if "[수산]" in title or "[농할]" in title:
            new_posts.append(entry)

    if new_posts:
        print(f"🎯 새로운 타겟 게시글 {len(new_posts)}개 발견!")
        for entry in reversed(new_posts):
            asyncio.run(send_telegram(entry.title, entry.link, entry.published))
        
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write(feed.entries[0].link)
        print("💾 최신 기록 업데이트 완료.")
    else:
        print("📭 새로운 [수산]/[농할] 소식이 없습니다.")

if __name__ == "__main__":
    run_rss_check()
