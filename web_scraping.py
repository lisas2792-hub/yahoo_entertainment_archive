import time
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config import (
    YAHOO_URL,
    HEADLESS,
    PAGE_WAIT_SECONDS
)


def create_driver():

    options = Options()

    if HEADLESS:
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1400,1200")
    options.add_argument("--lang=zh-TW")

    service = Service(
        ChromeDriverManager().install()
    )

    return webdriver.Chrome(
        service=service,
        options=options
    )


def scrape_news():

    driver = create_driver()

    try:

        print("開啟 Yahoo 娛樂即時新聞頁面...")

        driver.get(YAHOO_URL)

        time.sleep(PAGE_WAIT_SECONDS)

        soup = BeautifulSoup(
            driver.page_source,
            "html.parser"
        )

        news_list = []

        # for a_tag in soup.select("a[href]"):

        #     title = a_tag.get_text(strip=True)
        #     href = a_tag.get("href")

        #     # 沒有標題 跳過
        #     if not title:
        #         continue

        #     # 沒有連結 跳過
        #     if not href:
        #         continue

        #     # 過濾非娛樂即時新聞網址
        #     if "/news/" not in href:
        #         continue

        for a_tag in soup.select("a[href]"):

            title = a_tag.get_text(strip=True)
            href = a_tag.get("href")

            print("TITLE:", title)
            print("URL:", href)
            print("-" * 50)

        df = pd.DataFrame(news_list)

        # 網址去重複，防止重爬
        if not df.empty:
            df = df.drop_duplicates(
                subset=["url"]
            )

        return df

    finally:

        print("關閉瀏覽器")

        driver.quit()