# app/bot/scraper.py

import requests
from bs4 import BeautifulSoup
import re
import time
import json
import os
from urllib.parse import urljoin
from difflib import get_close_matches
from typing import List, Tuple, Dict, Any

# optional fast fuzzy
try:
    from rapidfuzz import process, fuzz
    HAVE_RAPIDFUZZ = True
except Exception:
    HAVE_RAPIDFUZZ = False

BASE = "https://www.tablycjakalorijnosti.com.ua"
CATALOG_PATH = "/tablytsya-yizhyi"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PlateMateBot/1.0)"}

# cache dir next to this file's parent (project root)/cache_tablycja
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # if file in app/bot, BASE_DIR -> app
CACHE_DIR = os.path.join(BASE_DIR, "cache")
PRODUCT_LIST_FN = os.path.join(CACHE_DIR, "products.json")
NUTRI_CACHE_FN = os.path.join(CACHE_DIR, "nutrition_cache.json")

os.makedirs(CACHE_DIR, exist_ok=True)

# --- networking helper ---
def polite_get(url, session=None, sleep=0.5, max_retries=3):
    s = session or requests
    for attempt in range(max_retries):
        try:
            resp = s.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            time.sleep(sleep)  # be polite
            return resp.text
        except Exception as e:
            # Keep warning short
            print(f"[WARN] GET {url} failed: {e} — retry {attempt+1}/{max_retries}")
            time.sleep(1 + attempt * 1.0)
    raise RuntimeError(f"Failed to GET {url} after {max_retries} retries")

# --- parse helpers ---
def parse_catalog_page(html: str):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(strip=True)
        if not text:
            continue
        if href.startswith("/stravy/") or href.startswith("/stravy"):
            if len(text) > 1:
                items.append((text, href))
    seen = set()
    uniq = []
    for name, href in items:
        key = (name.lower(), href)
        if key not in seen:
            seen.add(key)
            uniq.append((name, href))
    return uniq

RE_ENERGY = re.compile(r'([0-9]+(?:[.,][0-9]+)?)\s*(?:ккал|kcal)', flags=re.I)
RE_PROTEIN = re.compile(r'Білки[:\s]*([0-9]+(?:[.,][0-9]+)?)\s*г', flags=re.I)
RE_CARBS = re.compile(r'Вуглеводи[:\s]*([0-9]+(?:[.,][0-9]+)?)\s*г', flags=re.I)
RE_FAT = re.compile(r'Жири[:\s]*([0-9]+(?:[.,][0-9]+)?)\s*г', flags=re.I)
RE_FIBER = re.compile(r'(?:Волокна|Клітковина|Волокна)[:\s]*([0-9]+(?:[.,][0-9]+)?)\s*г', flags=re.I)
RE_SUGAR = re.compile(r'Цукор[:\s]*([0-9]+(?:[.,][0-9]+)?)\s*г', flags=re.I)

def parse_product_page(html: str) -> Dict[str, Any]:
    text = BeautifulSoup(html, "html.parser").get_text(separator="\n")
    def find_first(pattern):
        m = pattern.search(text)
        if not m:
            return None
        val = m.group(1).replace(",", ".")
        try:
            return float(val)
        except:
            return None

    energy = find_first(RE_ENERGY)
    protein = find_first(RE_PROTEIN)
    carbs = find_first(RE_CARBS)
    fat = find_first(RE_FAT)
    fiber = find_first(RE_FIBER)
    sugar = find_first(RE_SUGAR)

    if energy is None:
        m = re.search(r'Енергія.*?([0-9]+(?:[.,][0-9]+)?)\s*(?:ккал|kcal)', text, flags=re.I|re.S)
        if m:
            energy = float(m.group(1).replace(",", "."))

    return {
        "energy_kcal": energy,
        "protein_g": protein,
        "carbs_g": carbs,
        "fat_g": fat,
        "fiber_g": fiber,
        "sugar_g": sugar
    }

# --- product list builder ---
def build_product_list(max_pages=50, sleep=0.5, force_refresh=False):
    if os.path.exists(PRODUCT_LIST_FN) and not force_refresh:
        with open(PRODUCT_LIST_FN, "r", encoding="utf-8") as f:
            return json.load(f)

    products = []
    seen_urls = set()
    session = requests.Session()

    for page in range(1, max_pages + 1):
        url = f"{BASE}{CATALOG_PATH}?page={page}"
        try:
            html = polite_get(url, session=session, sleep=sleep)
        except Exception as e:
            print(f"[WARN] stopping crawl: {e}")
            break
        items = parse_catalog_page(html)
        if not items:
            break
        for name, href in items:
            full = urljoin(BASE, href)
            if full in seen_urls:
                continue
            seen_urls.add(full)
            products.append({"name": name, "url": full})
    with open(PRODUCT_LIST_FN, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    return products

# --- nutrition cache ---
def load_nutrition_cache():
    if os.path.exists(NUTRI_CACHE_FN):
        with open(NUTRI_CACHE_FN, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_nutrition_cache(cache):
    with open(NUTRI_CACHE_FN, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def get_product_nutrition(product_url: str, session=None, sleep=0.5, use_cache=True):
    cache = load_nutrition_cache()
    if use_cache and product_url in cache:
        return cache[product_url]

    session = session or requests
    html = polite_get(product_url, session=session, sleep=sleep)
    data = parse_product_page(html)
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("h1") or soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None
    if title:
        data["title"] = title
    cache[product_url] = data
    save_nutrition_cache(cache)
    return data

# --- matching ---
def find_best_match(query: str, products: List[Dict[str,str]], limit=5):
    names = [p["name"] for p in products]
    q = query.strip().lower()
    for p in products:
        if p["name"].strip().lower() == q:
            return [(p["name"], p["url"], 100.0)]
    if HAVE_RAPIDFUZZ:
        choices = {p["name"]: p["url"] for p in products}
        top = process.extract(query, choices.keys(), scorer=fuzz.WRatio, limit=limit)
        return [(t[0], choices[t[0]], float(t[1])) for t in top]
    else:
        matches = get_close_matches(query, names, n=limit, cutoff=0.4)
        results = []
        for m in matches:
            score = (len(m) - abs(len(m) - len(query))) / max(len(m), len(query)) * 100
            url = next(p["url"] for p in products if p["name"] == m)
            results.append((m, url, score))
        return results
