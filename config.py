import os

# Yahoo 娛樂即時新聞來源
YAHOO_URL = "https://tw.news.yahoo.com/entertainment/archive/"

# Selenium

# 無頭模式(正式用)
HEADLESS = True
# 有頭模式(測試/debug用)
# HEADLESS = False

PAGE_WAIT_SECONDS = 3
MAX_SCROLL = 30

# 每次捲動像素與等待秒數（太短只會抓到第一屏）
SCROLL_STEP = 800
SCROLL_PAUSE_SECONDS = 2
# 連續幾輪沒抓到新資料就提前停止
STOP_AFTER_NO_NEW_ROUNDS = 2

# 邊爬邊篩：只保留 N 小時內新聞
NEWS_MAX_HOURS = 12

# 檔案路徑
RAW_DATA_PATH = "data/raw/news_raw.csv"
CLEANED_DATA_PATH = "data/cleaned/news_cleaned.csv"
OUTPUT_DATA_PATH = "data/output/news_final.csv"

# LLM（預設使用本機 Ollama，連不上會在自動 fallback）
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "250"))