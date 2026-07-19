# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MASTER_CSV = DATA_DIR / "detailed_products_master.csv"
CUSTOM_CSV = DATA_DIR / "custom_products.csv"
EVERGREEN_CSV = DATA_DIR / "evergreen_products.csv"

REQUIRED_COLUMNS = {"대분류", "기준품목", "세부품목"}
DEFAULT_EVERGREEN = ["쌀", "잡곡", "현미", "백미", "콩", "소고기", "돼지고기", "닭고기", "계란", "라면", "햄", "소시지"]


def load_master_df() -> pd.DataFrame:
    """행 수를 고정하지 않고 필수 열과 유효 데이터만 검증한다."""
    if not MASTER_CSV.exists():
        raise RuntimeError(f"필수 DB 파일이 없습니다: {MASTER_CSV}")
    try:
        df = pd.read_csv(MASTER_CSV, encoding="utf-8-sig", dtype=str).fillna("")
    except UnicodeDecodeError:
        df = pd.read_csv(MASTER_CSV, encoding="utf-8", dtype=str).fillna("")

    df.columns = df.columns.astype(str).str.strip()
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise RuntimeError("마스터 DB 필수 열 누락: " + ", ".join(sorted(missing)))

    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    df = df[(df["대분류"] != "") & (df["세부품목"] != "")]
    df = df.drop_duplicates(["대분류", "세부품목"], keep="first").reset_index(drop=True)
    if df.empty:
        raise RuntimeError("마스터 DB에 분석할 품목이 없습니다.")
    return df


def expected_counts() -> Dict[str, int]:
    df = load_master_df()
    return df.groupby("대분류", sort=False)["세부품목"].nunique().to_dict()


# 기존 app.py 호환용. 고정값이 아니라 현재 파일에서 자동 계산된다.
EXPECTED_COUNTS = expected_counts()


def load_custom_df() -> pd.DataFrame:
    cols = ["대분류", "기준품목", "세부품목"]
    if not CUSTOM_CSV.exists():
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(CUSTOM_CSV, encoding="utf-8-sig", dtype=str).fillna("")
    for col in cols:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].astype(str).str.strip()
    return df[(df["대분류"] != "") & (df["세부품목"] != "")][cols].drop_duplicates()


def load_database_df() -> pd.DataFrame:
    master = load_master_df().copy()
    master["구분"] = "기본DB"
    custom = load_custom_df().copy()
    custom["구분"] = "사용자추가"
    # 사용자 DB에는 확장 열이 없어도 concat 가능
    df = pd.concat([master, custom], ignore_index=True, sort=False).fillna("")
    return df.drop_duplicates(["대분류", "세부품목"], keep="first").reset_index(drop=True)


def category_map() -> Dict[str, List[str]]:
    df = load_database_df()
    return {
        category: group["세부품목"].drop_duplicates().tolist()
        for category, group in df.groupby("대분류", sort=False)
    }


def add_custom(category: str, base_product: str, items: List[str]) -> int:
    current = load_custom_df()
    rows = [
        {"대분류": category.strip(), "기준품목": base_product.strip(), "세부품목": x.strip()}
        for x in items if x.strip()
    ]
    if not rows:
        return 0
    before = len(current)
    out = pd.concat([current, pd.DataFrame(rows)], ignore_index=True)
    out = out.drop_duplicates(["대분류", "세부품목"], keep="first")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(CUSTOM_CSV, index=False, encoding="utf-8-sig")
    return len(out) - before


def delete_custom(category: str, items: List[str]) -> int:
    current = load_custom_df()
    targets = {x.strip() for x in items if x.strip()}
    mask = (current["대분류"] == category) & current["세부품목"].isin(targets)
    removed = int(mask.sum())
    current.loc[~mask].to_csv(CUSTOM_CSV, index=False, encoding="utf-8-sig")
    return removed


def load_evergreen() -> List[str]:
    if not EVERGREEN_CSV.exists():
        save_evergreen(DEFAULT_EVERGREEN)
    try:
        df = pd.read_csv(EVERGREEN_CSV, encoding="utf-8-sig", dtype=str).fillna("")
        return [x.strip() for x in df.get("품목", pd.Series(dtype=str)).tolist() if x.strip()]
    except Exception:
        return list(DEFAULT_EVERGREEN)


def save_evergreen(items: List[str]) -> None:
    values = list(dict.fromkeys(x.strip() for x in items if x.strip()))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"품목": values}).to_csv(EVERGREEN_CSV, index=False, encoding="utf-8-sig")
