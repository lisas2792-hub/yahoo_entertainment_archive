import re
import time
from datetime import timedelta

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config import (
    YAHOO_URL,
    HEADLESS,
    PAGE_WAIT_SECONDS,
    MAX_SCROLL,
    SCROLL_STEP,
    SCROLL_PAUSE_SECONDS,
    STOP_AFTER_NO_NEW_ROUNDS,
    NEWS_MAX_HOURS,
)

# 建立 自動化 Chrome 瀏覽器
def create_driver():
    options = Options()

    if HEADLESS:
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1400,1200")
    options.add_argument("--lang=zh-TW")

    service = Service(ChromeDriverManager().install())

    return webdriver.Chrome(
        service=service,
        options=options
    )

# 拆開來源與時間
def parse_source_and_time(meta_text: str) -> tuple[str, str]:
    meta_text = (meta_text or "").strip()
    if not meta_text:
        return "", ""

    if "・" in meta_text:
        source, published_at = meta_text.rsplit("・", 1)
        return source.strip(), published_at.strip()

    return meta_text, ""

# 時間篩選
def time_limit(published_at: str, max_hours: int) -> bool:
    text = (published_at or "").strip()
    if not text:
        return False

    minute_match = re.search(r"(\d+)\s*分鐘前", text)
    if minute_match:
        minutes = int(minute_match.group(1))
        return timedelta(minutes=minutes) <= timedelta(hours=max_hours)

    hour_match = re.search(r"(\d+)\s*小時前", text)
    if hour_match:
        hours = int(hour_match.group(1))
        return timedelta(hours=hours) <= timedelta(hours=max_hours)

    if "昨天" in text:
        return False

    # 格式未知，先保留
    return True

# 過濾抓取網頁(抓列表區域):新聞的標題、連結、來源、時間、摘要預覽整理成 list
def extract_cards(soup: BeautifulSoup) -> list[dict]:
    news_list = []

    for card in soup.select("li.stream-card"):
        link = card.select_one("h3 a[href]")
        if not link:
            continue

        title = link.get_text(strip=True)
        href = link.get("href", "").split("?")[0]

        if not title or not href:
            continue

        if "tw.news.yahoo.com" not in href:
            continue

        meta_tag = card.select_one("div.text-px12.text-dolphin")
        meta_text = meta_tag.get_text(" ", strip=True) if meta_tag else ""
        source, published_at = parse_source_and_time(meta_text)
        if not time_limit(published_at, NEWS_MAX_HOURS):
            continue

        summary_tag = card.select_one("p")
        summary = summary_tag.get_text(" ", strip=True) if summary_tag else ""
        summary = re.sub(r"\s+", " ", summary).strip()

        news_list.append(
            {
                "title": title,
                "url": href,
                "source": source,
                "published_at": published_at,
                "summary_preview": summary,
            }
        )

    return news_list

# 主要(爬取 Yahoo 娛樂即時新聞)
def scrape_news():
    driver = create_driver()

    try:
        print("開啟 Yahoo 娛樂即時新聞頁面")

        # 開啟娛樂 archive 頁
        driver.get(YAHOO_URL)
        time.sleep(PAGE_WAIT_SECONDS)

        news_list = []
        seen_urls = set()
        no_new_rounds = 0

        for _ in range(MAX_SCROLL):
            soup = BeautifulSoup(driver.page_source, "html.parser")
            round_new_items = 0

            # 解析娛樂主列表區塊，避免側欄與廣告連結
            for item in extract_cards(soup):
                if item["url"] in seen_urls:
                    continue
                seen_urls.add(item["url"])
                news_list.append(item)
                round_new_items += 1

            if round_new_items == 0:
                no_new_rounds += 1
            else:
                no_new_rounds = 0

            if no_new_rounds >= STOP_AFTER_NO_NEW_ROUNDS:
                print(
                    f"連續 {STOP_AFTER_NO_NEW_ROUNDS} 輪沒有新資料，提前停止捲動"
                )
                break

            # 分段往下捲，等待 lazy load（一次捲到底，沒載入更多，無法跑出，常只留第一屏約 18 則）
            for _ in range(3):
                driver.execute_script(
                    f"window.scrollBy(0, {SCROLL_STEP});"
                )
                time.sleep(SCROLL_PAUSE_SECONDS)

        df = pd.DataFrame(news_list)

        # URL去重:防止重複寫入
        if not df.empty:
            df = df.drop_duplicates(subset=["url"])

        print(f"取得 {len(df)} 筆娛樂新聞")
        return df

    finally:
        print("關閉瀏覽器")
        driver.quit()
