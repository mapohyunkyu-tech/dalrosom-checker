# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
from typing import Dict, List
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MASTER_CSV = DATA_DIR / "detailed_products_943.csv"
CUSTOM_CSV = DATA_DIR / "custom_products.csv"
EVERGREEN_CSV = DATA_DIR / "evergreen.csv"
EXPECTED_COUNTS = {"과일": 298, "채소": 300, "수산물": 248, "버섯": 48, "견과·특용": 49}
DEFAULT_EVERGREEN = ["쌀", "잡곡", "현미", "백미", "콩", "소고기", "돼지고기", "닭고기", "계란", "라면", "햄", "소시지"]


def load_master_df() -> pd.DataFrame:
    if not MASTER_CSV.exists():
        raise RuntimeError(f"필수 DB 파일이 없습니다: {MASTER_CSV}")
    df = pd.read_csv(MASTER_CSV, encoding="utf-8-sig", dtype=str).fillna("")
    required = {"대분류", "기준품목", "세부품목"}
    if not required.issubset(df.columns):
        raise RuntimeError("마스터 DB 열 구성이 올바르지 않습니다.")
    df["대분류"] = df["대분류"].str.strip()
    df["기준품목"] = df["기준품목"].str.strip()
    df["세부품목"] = df["세부품목"].str.strip()
    df = df[(df["대분류"] != "") & (df["세부품목"] != "")].drop_duplicates(["대분류", "세부품목"])
    counts = df.groupby("대분류")["세부품목"].nunique().to_dict()
    if len(df) != 943 or any(counts.get(k, 0) != v for k, v in EXPECTED_COUNTS.items()):
        raise RuntimeError(f"마스터 DB 검증 실패: 총 {len(df)}개 / {counts}")
    return df.reset_index(drop=True)


def load_custom_df() -> pd.DataFrame:
    if not CUSTOM_CSV.exists():
        return pd.DataFrame(columns=["대분류", "기준품목", "세부품목"])
    df = pd.read_csv(CUSTOM_CSV, encoding="utf-8-sig", dtype=str).fillna("")
    for col in ["대분류", "기준품목", "세부품목"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].str.strip()
    return df[(df["대분류"] != "") & (df["세부품목"] != "")][["대분류", "기준품목", "세부품목"]].drop_duplicates()


def load_database_df() -> pd.DataFrame:
    master = load_master_df()[["대분류", "기준품목", "세부품목"]].copy()
    master["구분"] = "기본DB"
    custom = load_custom_df().copy()
    custom["구분"] = "사용자추가"
    df = pd.concat([master, custom], ignore_index=True)
    return df.drop_duplicates(["대분류", "세부품목"], keep="first").reset_index(drop=True)


def category_map() -> Dict[str, List[str]]:
    df = load_database_df()
    return {
        category: group["세부품목"].drop_duplicates().tolist()
        for category, group in df.groupby("대분류", sort=False)
    }


def add_custom(category: str, base_product: str, items: List[str]) -> int:
    current = load_custom_df()
    rows = [{"대분류": category.strip(), "기준품목": base_product.strip(), "세부품목": x.strip()} for x in items if x.strip()]
    if not rows:
        return 0
    before = len(current)
    out = pd.concat([current, pd.DataFrame(rows)], ignore_index=True).drop_duplicates(["대분류", "세부품목"])
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
    pd.DataFrame({"품목": values}).to_csv(EVERGREEN_CSV, index=False, encoding="utf-8-sig")
