# utils/price_cache.py

import os
import requests
import json
from datetime import datetime
from time import sleep

PRICE_CACHE_FILE = "data/price_cache.json"
CRYPTOCOMPARE_BASE_URL = "https://min-api.cryptocompare.com/data/v2/histoday"

def load_price_cache():
    if os.path.exists(PRICE_CACHE_FILE):
        with open(PRICE_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_price_cache(cache):
    os.makedirs("data", exist_ok=True)
    with open(PRICE_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def get_price_usd(symbol: str, contract_address: str, timestamp_iso: str, cache: dict) -> float:
    """
    Returns historical USD price for a given token symbol using CryptoCompare daily close.
    Falls back to 0.0 if not available. Symbol must be listed on CryptoCompare.
    """
    if not symbol or not timestamp_iso:
        return 0.0

    symbol = symbol.upper()
    date_str = timestamp_iso.split("T")[0]
    cache_key = f"{symbol}-{date_str}"
    if cache_key in cache:
        return cache[cache_key]

    try:
        timestamp = int(datetime.fromisoformat(timestamp_iso.replace("Z", "")).timestamp())
        url = f"{CRYPTOCOMPARE_BASE_URL}?fsym={symbol}&tsym=USD&toTs={timestamp}&limit=1"

        res = requests.get(url)
        if res.status_code != 200:
            print(f"❌ CryptoCompare error: {symbol} on {date_str} — HTTP {res.status_code}")
            return 0.0

        data = res.json()
        if "Data" in data and "Data" in data["Data"] and data["Data"]["Data"]:
            price = data["Data"]["Data"][0].get("close", 0.0)
            if price:
                cache[cache_key] = price
                sleep(0.1)
                return price

        print(f"💸 No CryptoCompare price for {symbol} on {date_str}")
        return 0.0

    except Exception as e:
        print(f"❌ Exception fetching {symbol} on {date_str}: {e}")
        return 0.0
