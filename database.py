# -*- coding: utf-8 -*-
from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Dict, List

DATA_DIR = Path(__file__).parent / "data"
DB_FILE = DATA_DIR / "products.json"
MASTER_CSV = DATA_DIR / "detailed_products_943.csv"
EVERGREEN_FILE = DATA_DIR / "evergreen.json"
DEFAULT_EVERGREEN = ["쌀", "잡곡", "현미", "백미", "콩", "소고기", "돼지고기", "닭고기", "계란", "라면", "햄", "소시지"]
EXPECTED_COUNTS = {"과일": 298, "채소": 300, "수산물": 248, "버섯": 48, "견과·특용": 49}


def _write(path: Path, value) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_master_csv() -> Dict[str, List[str]]:
    """943개 마스터 CSV를 최우선 원본으로 읽습니다."""
    result: Dict[str, List[str]] = {}
    with MASTER_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            category = str(row.get("대분류", "")).strip()
            item = str(row.get("세부품목", "")).strip()
            if category and item:
                result.setdefault(category, []).append(item)
    return {k: list(dict.fromkeys(v)) for k, v in result.items()}


def _valid_master(data: Dict[str, List[str]]) -> bool:
    return all(len(data.get(k, [])) == v for k, v in EXPECTED_COUNTS.items()) and sum(map(len, data.values())) == 943


def load_products() -> Dict[str, List[str]]:
    """항상 CSV의 943개 기본 DB를 사용하고, products.json의 사용자 추가분만 병합합니다."""
    master = _load_master_csv()
    if not _valid_master(master):
        raise RuntimeError(
            "세부품목 마스터 DB가 손상되었습니다. "
            f"현재 개수: {sum(len(v) for v in master.values())}, 기대 개수: 943"
        )

    saved: Dict[str, List[str]] = {}
    if DB_FILE.exists():
        try:
            loaded = json.loads(DB_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                saved = loaded
        except Exception:
            saved = {}

    merged: Dict[str, List[str]] = {}
    categories = list(dict.fromkeys([*master.keys(), *saved.keys()]))
    for category in categories:
        base = [str(x).strip() for x in master.get(category, []) if str(x).strip()]
        custom = [str(x).strip() for x in saved.get(category, []) if str(x).strip()]
        merged[category] = list(dict.fromkeys(base + custom))

    if saved != merged:
        _write(DB_FILE, merged)
    return merged


def save_products(data: Dict[str, List[str]]) -> None:
    cleaned = {k: list(dict.fromkeys(x.strip() for x in v if x.strip())) for k, v in data.items()}
    _write(DB_FILE, cleaned)


def reset_products() -> None:
    master = _load_master_csv()
    if not _valid_master(master):
        raise RuntimeError("943개 마스터 CSV를 읽지 못했습니다.")
    _write(DB_FILE, master)


def load_evergreen() -> List[str]:
    if not EVERGREEN_FILE.exists():
        _write(EVERGREEN_FILE, DEFAULT_EVERGREEN)
    try:
        return list(dict.fromkeys(json.loads(EVERGREEN_FILE.read_text(encoding="utf-8"))))
    except Exception:
        return list(DEFAULT_EVERGREEN)


def save_evergreen(items: List[str]) -> None:
    _write(EVERGREEN_FILE, sorted(set(x.strip() for x in items if x.strip())))
