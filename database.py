# -*- coding: utf-8 -*-
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List
from products import PRODUCTS

DATA_DIR = Path(__file__).parent / "data"
DB_FILE = DATA_DIR / "products.json"
EVERGREEN_FILE = DATA_DIR / "evergreen.json"
DEFAULT_EVERGREEN = ["쌀", "잡곡", "현미", "백미", "콩", "소고기", "돼지고기", "닭고기", "계란", "라면", "햄", "소시지"]

def _write(path: Path, value) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

def load_products() -> Dict[str, List[str]]:
    """기본 세부품목 DB를 항상 보존하면서 사용자 추가 품목을 병합합니다.

    이전 버전의 축약 products.json(약 200여 개)이 GitHub/Cloud에 남아 있어도
    새 기본 DB 943개가 자동으로 복구되도록 합니다.
    """
    saved = {}
    if DB_FILE.exists():
        try:
            saved = json.loads(DB_FILE.read_text(encoding="utf-8"))
        except Exception:
            saved = {}

    merged: Dict[str, List[str]] = {}
    categories = list(dict.fromkeys(list(PRODUCTS.keys()) + list(saved.keys())))
    for category in categories:
        base = [str(x).strip() for x in PRODUCTS.get(category, []) if str(x).strip()]
        custom = [str(x).strip() for x in saved.get(category, []) if str(x).strip()]
        merged[category] = list(dict.fromkeys(base + custom))

    # 축약 DB가 남아 있거나 기본 품목이 빠졌다면 즉시 최신 병합본으로 갱신
    if saved != merged:
        _write(DB_FILE, merged)
    return merged

def save_products(data: Dict[str, List[str]]) -> None:
    cleaned = {k: sorted(set(x.strip() for x in v if x.strip())) for k, v in data.items()}
    _write(DB_FILE, cleaned)

def reset_products() -> None:
    _write(DB_FILE, PRODUCTS)

def load_evergreen() -> List[str]:
    if not EVERGREEN_FILE.exists():
        _write(EVERGREEN_FILE, DEFAULT_EVERGREEN)
    try:
        return list(dict.fromkeys(json.loads(EVERGREEN_FILE.read_text(encoding="utf-8"))))
    except Exception:
        return list(DEFAULT_EVERGREEN)

def save_evergreen(items: List[str]) -> None:
    _write(EVERGREEN_FILE, sorted(set(x.strip() for x in items if x.strip())))
