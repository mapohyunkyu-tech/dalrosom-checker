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
    if not DB_FILE.exists():
        _write(DB_FILE, PRODUCTS)
    try:
        data = json.loads(DB_FILE.read_text(encoding="utf-8"))
        return {str(k): list(dict.fromkeys(map(str, v))) for k, v in data.items()}
    except Exception:
        return {k: list(v) for k, v in PRODUCTS.items()}

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
