
from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz, process
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

FROZEN = bool(getattr(sys, "frozen", False))
APP_DIR = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))

BASE_DIR = APP_DIR
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "output"
HISTORY_FILE = DATA_DIR / "history.csv"
MASTER_FILE = RESOURCE_DIR / "master_db.csv"
CONFIG_FILE = RESOURCE_DIR / "config.json"

DATA_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)

def log(message: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {message}", flush=True)

def normalize(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.lower().strip()
    return re.sub(r"[^0-9a-z\uac00-\ud7a3]+", "", text)

def load_config() -> dict:
    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

def build_driver(config: dict) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--lang=ko-KR")
    profile_dir = BASE_DIR / "chrome_profile"
    options.add_argument(f"--user-data-dir={profile_dir}")
    if config.get("headless", False):
        options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    return driver

def rank_keyword_pairs_from_dom(driver: webdriver.Chrome) -> list[tuple[int, str]]:
    script = r"""
    const out = [];
    const seen = new Set();
    const nodes = [...document.querySelectorAll('li, tr, div, a, span')];
    for (const el of nodes) {
      const txt = (el.innerText || '').trim().replace(/\s+/g, ' ');
      if (!txt || txt.length > 100) continue;
      const m = txt.match(/^(\d{1,3})\s*[.\-:]?\s+(.{1,60})$/);
      if (!m) continue;
      const rank = Number(m[1]);
      const keyword = m[2].trim();
      if (rank < 1 || rank > 1000) continue;
      if (!keyword || /^\d+$/.test(keyword)) continue;
      const key = rank + '|' + keyword;
      if (!seen.has(key)) {
        seen.add(key);
        out.push([rank, keyword]);
      }
    }
    return out;
    """
    raw = driver.execute_script(script) or []
    pairs = []
    for rank, keyword in raw:
        keyword = str(keyword).strip()
        if 1 <= int(rank) <= 1000 and 1 <= len(keyword) <= 60:
            pairs.append((int(rank), keyword))
    return pairs

def pairs_from_page_text(driver: webdriver.Chrome) -> list[tuple[int, str]]:
    text = driver.find_element(By.TAG_NAME, "body").text
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    pairs = []
    for i, line in enumerate(lines):
        m = re.fullmatch(r"(\d{1,3})", line)
        if m and i + 1 < len(lines):
            rank = int(m.group(1))
            keyword = lines[i + 1]
            if 1 <= rank <= 1000 and 1 <= len(keyword) <= 60:
                pairs.append((rank, keyword))
        else:
            m2 = re.match(r"^(\d{1,3})\s*[.\-:]?\s+(.{1,60})$", line)
            if m2:
                pairs.append((int(m2.group(1)), m2.group(2).strip()))
    return pairs

def dedupe_pairs(pairs: list[tuple[int, str]]) -> list[tuple[int, str]]:
    best = {}
    for rank, keyword in pairs:
        key = normalize(keyword)
        if not key:
            continue
        if key not in best or rank < best[key][0]:
            best[key] = (rank, keyword)
    return sorted(best.values(), key=lambda x: (x[0], x[1]))

def click_next(driver: webdriver.Chrome) -> bool:
    # Text is encoded to keep source file ASCII-only.
    next_words = [
        "\ub2e4\uc74c",       # next
        "\ub354\ubcf4\uae30", # more
        "next", "more", ">"
    ]
    candidates = driver.find_elements(By.CSS_SELECTOR, "button, a")
    for el in candidates:
        try:
            if not el.is_displayed() or not el.is_enabled():
                continue
            text = (el.text or "").strip().lower()
            aria = (el.get_attribute("aria-label") or "").strip().lower()
            title = (el.get_attribute("title") or "").strip().lower()
            combined = " ".join([text, aria, title])
            if any(word in combined for word in next_words):
                driver.execute_script("arguments[0].click();", el)
                time.sleep(2)
                return True
        except Exception:
            continue
    return False

def collect_rankings(driver: webdriver.Chrome, config: dict) -> pd.DataFrame:
    all_pairs = []
    max_pages = int(config.get("max_pages", 30))
    stable_rounds = 0
    previous_count = 0

    for page_no in range(1, max_pages + 1):
        time.sleep(float(config.get("page_wait_seconds", 2)))
        pairs = dedupe_pairs(rank_keyword_pairs_from_dom(driver) + pairs_from_page_text(driver))
        all_pairs.extend(pairs)
        all_pairs = dedupe_pairs(all_pairs)
        log(f"Page {page_no}: {len(pairs)} found, {len(all_pairs)} unique total")

        # Scroll to trigger lazy loading.
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
        more_pairs = dedupe_pairs(rank_keyword_pairs_from_dom(driver) + pairs_from_page_text(driver))
        all_pairs = dedupe_pairs(all_pairs + more_pairs)

        if len(all_pairs) == previous_count:
            stable_rounds += 1
        else:
            stable_rounds = 0
        previous_count = len(all_pairs)

        if len(all_pairs) >= int(config.get("target_count", 500)):
            break
        if stable_rounds >= 2 and not click_next(driver):
            break

    if not all_pairs:
        raise RuntimeError(
            "No ranking rows were detected. Open the ranking list in the browser, "
            "then return to this window and run again."
        )

    today = pd.Timestamp.today().normalize()
    return pd.DataFrame({
        "collection_date": [today] * len(all_pairs),
        "rank": [x[0] for x in all_pairs],
        "keyword": [x[1] for x in all_pairs],
    }).sort_values(["rank", "keyword"]).drop_duplicates("keyword")

def load_master() -> pd.DataFrame:
    master = pd.read_csv(MASTER_FILE, encoding="utf-8-sig")
    master["norm_item"] = master["detail_item"].map(normalize)
    master["norm_alias"] = master["aliases"].fillna("").map(normalize)
    return master

def classify(df: pd.DataFrame, master: pd.DataFrame) -> pd.DataFrame:
    exact = {}
    for _, row in master.iterrows():
        for key in [row["norm_item"], row["norm_alias"]]:
            if key:
                exact.setdefault(key, row["detail_item"])

    keys = master["norm_item"].dropna().tolist()
    key_name = dict(zip(master["norm_item"], master["detail_item"]))

    results = []
    for keyword in df["keyword"]:
        nq = normalize(keyword)
        if nq in exact:
            results.append(("EXISTS", exact[nq], 100))
            continue

        contains = master[
            master["norm_item"].map(lambda x: bool(x) and (x in nq or nq in x))
        ]
        if len(contains):
            results.append(("SIMILAR", contains.iloc[0]["detail_item"], 95))
            continue

        hit = process.extractOne(nq, keys, scorer=fuzz.ratio)
        if hit and hit[1] >= 82:
            results.append(("SIMILAR", key_name.get(hit[0], hit[0]), int(hit[1])))
        else:
            results.append(("NEW_CANDIDATE", "", int(hit[1]) if hit else 0))

    out = df.copy()
    out[["db_status", "matched_item", "similarity"]] = pd.DataFrame(results, index=out.index)
    return out

def add_history(today_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if HISTORY_FILE.exists():
        hist = pd.read_csv(HISTORY_FILE, encoding="utf-8-sig")
        hist["collection_date"] = pd.to_datetime(hist["collection_date"], errors="coerce")
    else:
        hist = pd.DataFrame(columns=["collection_date", "rank", "keyword"])

    prev_date = hist["collection_date"].max() if len(hist) else pd.NaT
    if pd.notna(prev_date):
        prev = hist[hist["collection_date"] == prev_date][["keyword", "rank"]].rename(
            columns={"rank": "previous_rank"}
        )
        today_df = today_df.merge(prev, on="keyword", how="left")
    else:
        today_df["previous_rank"] = pd.NA

    today_df["rank_change"] = today_df["previous_rank"] - today_df["rank"]
    today_df["surge"] = today_df["rank_change"].fillna(0).ge(30)

    hist_new = pd.concat(
        [hist[["collection_date", "rank", "keyword"]],
         today_df[["collection_date", "rank", "keyword"]]],
        ignore_index=True
    ).drop_duplicates(["collection_date", "keyword"], keep="last")

    hist_new.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")
    return today_df, hist_new

def season_tables(master: pd.DataFrame) -> dict[str, pd.DataFrame]:
    today = pd.Timestamp.today().normalize()
    out = master.copy()
    for col in ["entry_date", "peak_date", "end_date"]:
        out[col] = pd.to_datetime(out[col], errors="coerce")
    out["days_to_entry"] = (out["entry_date"] - today).dt.days
    out["days_to_peak"] = (out["peak_date"] - today).dt.days
    out["days_to_end"] = (out["end_date"] - today).dt.days
    return {
        "ENTRY_14D": out[(out["days_to_entry"] >= 0) & (out["days_to_entry"] <= 14)].sort_values("days_to_entry"),
        "PEAK_14D": out[(out["days_to_peak"] >= -7) & (out["days_to_peak"] <= 14)].sort_values("days_to_peak"),
        "ENDING_14D": out[(out["days_to_end"] >= 0) & (out["days_to_end"] <= 14)].sort_values("days_to_end"),
        "MASTER_DB": out,
    }

def save_results(ranked: pd.DataFrame, history: pd.DataFrame, master: pd.DataFrame) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUT_DIR / f"market_scout_{stamp}.xlsx"
    seasons = season_tables(master)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        ranked.to_excel(writer, sheet_name="TODAY_RANKING", index=False)
        ranked[ranked["db_status"] == "NEW_CANDIDATE"].to_excel(
            writer, sheet_name="NEW_CANDIDATES", index=False
        )
        ranked[ranked["surge"]].sort_values("rank_change", ascending=False).to_excel(
            writer, sheet_name="SURGING", index=False
        )
        history.sort_values(["collection_date", "rank"]).to_excel(
            writer, sheet_name="HISTORY", index=False
        )
        for name, frame in seasons.items():
            frame.to_excel(writer, sheet_name=name[:31], index=False)

        for ws in writer.book.worksheets:
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for cell in ws[1]:
                cell.font = cell.font.copy(bold=True)
            for column in ws.columns:
                width = min(
                    max(max((len(str(c.value)) if c.value is not None else 0) for c in column[:200]) + 2, 10),
                    35,
                )
                ws.column_dimensions[column[0].column_letter].width = width
    return path

def main() -> int:
    config = load_config()
    master = load_master()
    log(f"Master DB loaded: {len(master)} rows")
    driver = None
    try:
        driver = build_driver(config)
        driver.get(config["start_url"])
        log("Browser opened.")
        print()
        print("In Chrome, open the desired Shopping Insight ranking page.")
        print("Select the category and date range if needed.")
        input("When the ranking list is visible, press ENTER here: ")

        ranked = collect_rankings(driver, config)
        ranked = classify(ranked, master)
        ranked, history = add_history(ranked)
        result = save_results(ranked, history, master)
        log(f"Saved: {result}")
        os.startfile(result)
        return 0
    except Exception as exc:
        log(f"ERROR: {exc}")
        with (OUT_DIR / "error_log.txt").open("a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().isoformat()}]\n{type(exc).__name__}: {exc}\n")
        input("Press ENTER to close.")
        return 1
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass

if __name__ == "__main__":
    raise SystemExit(main())
