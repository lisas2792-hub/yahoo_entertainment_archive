## Yahoo 娛樂新聞爬蟲（含清理與 LLM 分析）

從 Yahoo 娛樂 archive 頁面抓新聞，並輸出：
- `data/raw/news_raw.csv`（原始結果）
- `data/cleaned/news_cleaned.csv`（清理後結果）
- `data/output/news_final.csv`（LLM 分析結果）

目前流程：
1. Selenium 進入列表頁抓標題、連結、來源、時間。
2. 逐篇進文章頁抓正文內容（`content`）。
3. 以文章真實發佈時間優先做時間篩選（`NEWS_MAX_HOURS`）。
4. `clean.py` 做內容清理（移除導流語句、格式整理）。
5. `llm_analyzer.py` 產生摘要、NER、是否演唱會欄位。

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
- `OLLAMA_URL`：Ollama API 位址（預設 `http://localhost:11434/api/generate`）
- `OLLAMA_MODEL`：使用的模型（預設 `llama3.1:8b`）
- `LLM_TIMEOUT_SECONDS`：單次 LLM 呼叫 timeout 秒數

---

## 本機執行

直接跑完整流程（爬蟲 + 清理 + LLM）：

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

只跑 LLM 分析（讀 cleaned 輸出 final）：

```bash
py llm_analyzer.py
```

---

## LLM 使用說明（Ollama）

本專案預設使用本機 Ollama。

1. 安裝 Ollama：<https://ollama.com/download>  
2. 下載模型：

```bash
ollama pull qwen2.5:3b
```

3. 確認模型存在：

```bash
ollama list
```

### 若沒安裝或連不到 Ollama

- 程式會跑，不會中斷。
- 終端會印出 `[LLM提醒]` 訊息。
- fallback 規則如下：
  - `新聞內文摘要`：取前 100 字
  - `實體(人名/團體)`：`Null`
  - `是否為演唱會`：`Null`

---

## 輸出檔案

- `data/raw/news_raw.csv`
  - 欄位：`title`, `url`, `source`, `published_at`, `content`
- `data/cleaned/news_cleaned.csv`
  - 與 raw 欄位相同，但內容已做清洗與格式整理
- `data/output/news_final.csv`
  - 欄位：`新聞標題`, `新聞連結`, `新聞來源`, `新聞內文摘要`, `實體(人名/團體)`, `是否為演唱會`

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