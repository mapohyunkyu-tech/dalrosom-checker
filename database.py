# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
from typing import Dict, List
import pandas as pd
import base64
import gzip

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MASTER_CSV = DATA_DIR / "detailed_products_943.csv"
CUSTOM_CSV = DATA_DIR / "custom_products.csv"
EVERGREEN_CSV = DATA_DIR / "evergreen.csv"
EXPECTED_COUNTS = {"과일": 298, "채소": 300, "수산물": 248, "버섯": 48, "견과·특용": 49}
_EMBEDDED_MASTER_GZ_B64 = """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"""

DEFAULT_EVERGREEN = ["쌀", "잡곡", "현미", "백미", "콩", "소고기", "돼지고기", "닭고기", "계란", "라면", "햄", "소시지"]


def _restore_master_csv_if_missing() -> None:
    """GitHub 업로드에서 data 폴더가 누락돼도 내장 DB를 자동 복구합니다."""
    if MASTER_CSV.exists():
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        raw = gzip.decompress(base64.b64decode(_EMBEDDED_MASTER_GZ_B64.encode("ascii")))
        MASTER_CSV.write_bytes(raw)
    except Exception as exc:
        raise RuntimeError(f"마스터 DB 자동 복구 실패: {exc}") from exc


def load_master_df() -> pd.DataFrame:
    _restore_master_csv_if_missing()
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
