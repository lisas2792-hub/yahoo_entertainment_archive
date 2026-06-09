import os
import re
import pandas as pd

from config import RAW_DATA_PATH, CLEANED_DATA_PATH

# 清理文章內文(處理抓取的文章內文會有不是我要的內容問題)
def clean_content_text(text: str) -> str:
    content = (text or "").strip()
    if not content:
        return ""

    content = re.sub(r"\s+", " ", content).strip()

    drop_phrases = (
        "加入為 Google 偏好來源",
        "將 Yahoo 設為首選來源",
        "在 Google 上查看更多我們的精彩報導",
    )
    for phrase in drop_phrases:
        content = content.replace(phrase, "")

    # 移除文末連結等
    content = re.sub(r"更多[^。！？\n]{0,40}報導", "", content)
    content = re.sub(r"\s+", " ", content).strip()
    # 移除開頭的逗號、句號、空格等
    content = re.sub(r"^[，,。．、\s]+", "", content)
    return content

# 清理原始資料(做內容清洗與格式整理)
def clean_raw_news() -> pd.DataFrame:
    if not os.path.exists(RAW_DATA_PATH):
        raise FileNotFoundError(f"找不到 raw 檔案：{RAW_DATA_PATH}")

    df = pd.read_csv(RAW_DATA_PATH)
    if df.empty:
        return df

    if "url" in df.columns:
        df = df.drop_duplicates(subset=["url"])

    for col in ("title", "source", "published_at", "content"):
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    if "content" in df.columns:
        df["content"] = df["content"].apply(clean_content_text)

    os.makedirs(os.path.dirname(CLEANED_DATA_PATH), exist_ok=True)
    df.to_csv(CLEANED_DATA_PATH, index=False, encoding="utf-8-sig")
    return df


if __name__ == "__main__":
    cleaned = clean_raw_news()
    print(f"清理完成，共 {len(cleaned)} 筆")
    print(f"輸出檔案：{CLEANED_DATA_PATH}")
