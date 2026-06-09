import os

from clean import clean_raw_news
from config import RAW_DATA_PATH, CLEANED_DATA_PATH
from web_scraping import scrape_news


def main():

    print("執行 Yahoo 娛樂即時新聞爬蟲")

    # 執行爬蟲
    df = scrape_news()

    # 建立資料夾
    os.makedirs(
        os.path.dirname(RAW_DATA_PATH),
        exist_ok=True
    )

    # 輸出原始資料
    df.to_csv(
        RAW_DATA_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    # raw輸出後執行清理
    cleaned_df = clean_raw_news()

    print()
    print("===== 執行結果 =====")
    print(f"取得資料筆數：{len(df)}")
    print(f"輸出檔案：{RAW_DATA_PATH}")
    print(f"清理後筆數：{len(cleaned_df)}")
    print(f"清理檔案：{CLEANED_DATA_PATH}")
    print()

    print(df.head(10))


if __name__ == "__main__":
    main()