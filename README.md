## Yahoo 娛樂新聞爬蟲（含內容清理）

從 Yahoo 娛樂 archive 頁面抓新聞，並輸出：
- `data/raw/news_raw.csv`（原始結果）
- `data/cleaned/news_cleaned.csv`（清理後結果）

目前流程：
1. Selenium 進入列表頁抓標題、連結、來源、時間。
2. 逐篇進文章頁抓正文內容（`content`）。
3. 以文章真實發佈時間優先做時間篩選（`NEWS_MAX_HOURS`）。
4. `clean.py` 做內容清理（移除導流語句、格式整理）。

---

## 環境需求

- Python 3.10+（建議 3.11/3.12）
- Windows / macOS / Linux

安裝套件：

```bash
pip install -r requirements.txt
```

---

## 主要設定

在 `config.py` 可調整：

- `NEWS_MAX_HOURS`：只保留幾小時內新聞（例：`1`、`12`）
- `MAX_SCROLL`：最多捲動輪數（上限）
- `STOP_AFTER_NO_NEW_ROUNDS`：連續幾輪沒新資料就提前停止
- `HEADLESS`：`True` 背景跑、`False` 顯示瀏覽器

---

## 本機執行

直接跑完整流程（爬蟲 + 清理）：

```bash
py main.py
```

或：

```bash
python main.py
```

只跑清理：

```bash
py clean.py
```

---

## 輸出檔案

- `data/raw/news_raw.csv`
  - 欄位：`title`, `url`, `source`, `published_at`, `content`
- `data/cleaned/news_cleaned.csv`
  - 與 raw 欄位相同，但內容已做清洗與格式整理

---

## Docker

可用以下指令：

```bash
docker build -t yahoo-ent-crawler .
docker run --rm -v "${PWD}/data:/app/data" yahoo-ent-crawler
```

把輸出 CSV 保留在本機資料夾：
docker run --rm -v "${PWD}\data:/app/data" yahoo-ent-crawler

<!-- 只跑容器 ，快速驗證「容器可不可以跑」-->
docker run --rm yahoo-ent-crawler

