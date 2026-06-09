import os

import pandas as pd

from config import RAW_DATA_PATH, CLEANED_DATA_PATH


def clean_raw_news() -> pd.DataFrame:
    """輕量清理：去重與字串去空白。"""
    if not os.path.exists(RAW_DATA_PATH):
        raise FileNotFoundError(f"找不到 raw 檔案：{RAW_DATA_PATH}")

    df = pd.read_csv(RAW_DATA_PATH)
    if df.empty:
        return df

    if "url" in df.columns:
        df = df.drop_duplicates(subset=["url"])

    for col in ("title", "source", "published_at", "summary_preview"):
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    os.makedirs(os.path.dirname(CLEANED_DATA_PATH), exist_ok=True)
    df.to_csv(CLEANED_DATA_PATH, index=False, encoding="utf-8-sig")
    return df


if __name__ == "__main__":
    cleaned = clean_raw_news()
    print(f"清理完成，共 {len(cleaned)} 筆")
    print(f"輸出檔案：{CLEANED_DATA_PATH}")
