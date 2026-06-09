import json
import os
import re
from typing import Dict

import pandas as pd
import requests

from config import (
    CLEANED_DATA_PATH,
    OUTPUT_DATA_PATH,
    OLLAMA_URL,
    OLLAMA_MODEL,
    LLM_TIMEOUT_SECONDS,
)

_ollama_enabled = True
_fallback_warning_printed = False

# 檢查 Ollama 服務是否可用，不可的話會提醒
def check_ollama_available() -> bool:
    global _ollama_enabled, _fallback_warning_printed
    tags_url = OLLAMA_URL.replace("/api/generate", "/api/tags")
    try:
        res = requests.get(tags_url, timeout=5)
        res.raise_for_status()
        data = res.json() if res.content else {}
        models = [m.get("name", "") for m in data.get("models", []) if isinstance(m, dict)]
        if OLLAMA_MODEL not in models:
            _ollama_enabled = False
            if not _fallback_warning_printed:
                print("[LLM提醒] Ollama 已啟動，但找不到指定模型，將改用 fallback 規則模式。")
                print(f"[LLM提醒] 請先執行：ollama pull {OLLAMA_MODEL}")
                _fallback_warning_printed = True
            return False
        print(f"[LLM] 使用 Ollama 模型：{OLLAMA_MODEL}")
        return True
    except Exception as e:
        _ollama_enabled = False
        if not _fallback_warning_printed:
            print("[LLM提醒] 偵測不到 Ollama，將改用 fallback 規則模式。")
            print(f"[LLM提醒] 原因：{e}")
            _fallback_warning_printed = True
        return False

# 找不到Ollama時用的，摘要生成100字
def heuristic_summary(text: str, limit: int = 100) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return ""
    return text[:limit]


def heuristic_result(title: str, content: str) -> Dict[str, str]:
    return {
        "summary": heuristic_summary(content or title, limit=100),
        "entities": "Null",
        "is_concert_related": "Null",
    }

# LLM的prompt
def build_prompt(title: str, content: str) -> str:
    return f"""
    你是繁體中文新聞分析助理。請只輸出 JSON，不要有其他文字。

    欄位規則：
    1. summary：50 字內摘要。
    2. entities：人名或團體名，多個以逗號分隔；若無則填 Null。
    3. is_concert_related：判斷是否與演唱會相關，只能填「是」或「否」。

    新聞標題：{title}
    新聞內文：{content}
    """.strip()

def parse_llm_json(raw: str) -> Dict[str, str]:
    raw = (raw or "").strip()
    m = re.search(r"\{.*\}", raw, re.S)
    data = json.loads(m.group(0) if m else raw)
    summary = str(data.get("summary", "")).strip()
    entities = str(data.get("entities", "Null")).strip() or "Null"
    is_concert = str(data.get("is_concert_related", "Null")).strip()
    if is_concert not in ("是", "否"):
        is_concert = "Null"
    return {
        "summary": summary,
        "entities": entities,
        "is_concert_related": is_concert,
    }

def ollama_result(title: str, content: str) -> Dict[str, str]:
    global _ollama_enabled, _fallback_warning_printed
    if not _ollama_enabled:
        return heuristic_result(title, content)

    prompt = build_prompt(title, content)
    try:
        res = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=LLM_TIMEOUT_SECONDS,
        )
        res.raise_for_status()
        raw = res.json().get("response", "")
        parsed = parse_llm_json(raw)
        if not parsed["summary"]:
            parsed["summary"] = heuristic_summary(content or title, limit=100)
        if not parsed["entities"]:
            parsed["entities"] = "Null"
        return parsed
    except Exception as e:
        _ollama_enabled = False
        if not _fallback_warning_printed:
            print("[LLM提醒] Ollama 呼叫失敗，改用 fallback 規則模式。")
            print(f"[LLM提醒] 原因：{e}")
            _fallback_warning_printed = True
        return heuristic_result(title, content)

def run_llm_analysis() -> pd.DataFrame:
    if not os.path.exists(CLEANED_DATA_PATH):
        raise FileNotFoundError(f"找不到 cleaned 檔案：{CLEANED_DATA_PATH}")

    df = pd.read_csv(CLEANED_DATA_PATH)
    if df.empty:
        os.makedirs(os.path.dirname(OUTPUT_DATA_PATH), exist_ok=True)
        empty = pd.DataFrame(columns=[
            "新聞標題", "新聞連結", "新聞來源", "新聞內文摘要", "實體(人名/團體)", "是否為演唱會"
        ])
        empty.to_csv(OUTPUT_DATA_PATH, index=False, encoding="utf-8-sig")
        return empty

    check_ollama_available()

    rows = []
    for _, row in df.iterrows():
        title = str(row.get("title", "")).strip()
        url = str(row.get("url", "")).strip()
        source = str(row.get("source", "")).strip()
        content = str(row.get("content", "")).strip()

        if not content:
            content = title

        result = ollama_result(title, content)
        rows.append({
            "新聞標題": title,
            "新聞連結": url,
            "新聞來源": source,
            "新聞內文摘要": result["summary"],
            "實體(人名/團體)": result["entities"] or "Null",
            "是否為演唱會": result["is_concert_related"],
        })

    final_df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(OUTPUT_DATA_PATH), exist_ok=True)
    final_df.to_csv(OUTPUT_DATA_PATH, index=False, encoding="utf-8-sig")
    return final_df


if __name__ == "__main__":
    analyzed = run_llm_analysis()
    print(f"LLM分析完成，共 {len(analyzed)} 筆")
    print(f"輸出檔案：{OUTPUT_DATA_PATH}")
