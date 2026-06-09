import re
import time
import os
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
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
    
    # Docker/CI 環境常用參數，避免 sandbox 與共享記憶體問題
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    chrome_bin = os.getenv("CHROME_BIN")
    if chrome_bin:
        options.binary_location = chrome_bin

    chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
    if chromedriver_path:
        service = Service(chromedriver_path)
    else:
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

# 判斷文章真實發佈時間是否在 N 小時內
def is_within_hour_limit(dt_utc: datetime, max_hours: int) -> bool:
    now_utc = datetime.now(timezone.utc)
    return (now_utc - dt_utc) <= timedelta(hours=max_hours)

# 抓整篇內文與文章真實發佈時間(用 requests 進文章頁，抓 div.caas-body，並做換行清理)
def fetch_article_details(url: str) -> tuple[str, str, datetime | None]:
    try:
        res = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
            stream=True,
        )
        res.raise_for_status()
    except Exception:
        return "", "", None

    content_type = (res.headers.get("Content-Type") or "").lower()
    if "html" not in content_type:
        return "", "", None

    max_bytes = 2 * 1024 * 1024
    chunks = []
    total = 0
    for chunk in res.iter_content(chunk_size=8192):
        if not chunk:
            continue
        chunks.append(chunk)
        total += len(chunk)
        if total >= max_bytes:
            break

    raw_html = b"".join(chunks)
    encoding = res.encoding or "utf-8"
    html_text = raw_html.decode(encoding, errors="ignore")
    soup = BeautifulSoup(html_text, "html.parser")

    published_at = ""
    published_dt_utc = None

    time_tag = soup.select_one("time[datetime], time")
    if time_tag:
        raw_time = time_tag.get("datetime") or time_tag.get_text(" ", strip=True)
        try:
            dt = date_parser.parse(raw_time)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            published_dt_utc = dt.astimezone(timezone.utc)
            tw_time = published_dt_utc.astimezone(timezone(timedelta(hours=8)))
            published_at = tw_time.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            published_dt_utc = None

    body = soup.select_one("div.caas-body")
    if not body:
        body = soup.select_one("article")
    if not body:
        return "", published_at, published_dt_utc

    paragraphs = []
    for p_tag in body.select("p"):
        text = p_tag.get_text(" ", strip=True)
        if text:
            paragraphs.append(text)

    content = " ".join(paragraphs)
    return re.sub(r"\s+", " ", content).strip(), published_at, published_dt_utc

# 過濾抓取網頁(抓列表區域):新聞標題、連結、來源、時間、內容整理成 list
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

        summary_tag = card.select_one("p")
        summary = summary_tag.get_text(" ", strip=True) if summary_tag else ""
        summary = re.sub(r"\s+", " ", summary).strip()

        news_list.append(
            {
                "title": title,
                "url": href,
                "source": source,
                "published_at": published_at,
                "content": summary,
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
                    continue # 這篇URL以前抓過，跳過
                seen_urls.add(item["url"])

                # 抓整篇內文與真實發佈時間（抓到才覆蓋）
                article_content, article_published_at, article_dt_utc = fetch_article_details(item["url"])

                # 先用文章頁真實時間判斷，抓不到用列表相對時間判斷
                if article_dt_utc is not None:
                    if not is_within_hour_limit(article_dt_utc, NEWS_MAX_HOURS):
                        continue
                    item["published_at"] = article_published_at
                elif not time_limit(item["published_at"], NEWS_MAX_HOURS):
                    continue

                if article_content:
                    item["content"] = article_content

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
