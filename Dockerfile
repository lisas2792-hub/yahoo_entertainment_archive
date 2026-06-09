FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    OLLAMA_URL=http://host.docker.internal:11434/api/generate \
    OLLAMA_MODEL=qwen2.5:3b \
    LLM_TIMEOUT_SECONDS=250

WORKDIR /app

# 安裝 Chromium 與 ChromeDriver（給 Selenium 用）
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 執行完整流程
CMD ["python", "main.py"]
