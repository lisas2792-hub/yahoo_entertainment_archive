# import os

# from config import RAW_DATA_PATH
# from web_scraping import scrape_news


# def main():

#     print("開始執行 Yahoo 娛樂即時新聞爬蟲")

#     # 執行爬蟲
#     df = scrape_news()

#     # 建立資料夾
#     os.makedirs(
#         os.path.dirname(RAW_DATA_PATH),
#         exist_ok=True
#     )

#     # 輸出原始資料
#     df.to_csv(
#         RAW_DATA_PATH,
#         index=False,
#         encoding="utf-8-sig"
#     )

#     print()
#     print("===== 執行結果 =====")
#     print(f"取得資料筆數：{len(df)}")
#     print(f"輸出檔案：{RAW_DATA_PATH}")
#     print()

#     print(df.head(10))


# if __name__ == "__main__":
#     main()

from web_scraping import scrape_news

def main():
    scrape_news()

if __name__ == "__main__":
    main()