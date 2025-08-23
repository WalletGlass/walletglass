"""
price_cache.py — Alchemy-backed price fetcher with in-memory caching

Fetches historical USD prices for ETH and ERC-20 tokens using the Alchemy
/price/v1/tokens/historical API endpoint.

Used by: funding.py to value funding transfers in USD at time of receipt.
"""

import os
import requests
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
BASE_URL = "https://dashboard.alchemy.com/api/prices/v1/tokens/historical"

# Cache format: {(token.lower(), timestamp): price}
_price_cache = {}

def get_usd_price(token: str, timestamp: int) -> Optional[float]:
    """
    Fetches the USD price of `token` at the given UNIX timestamp.
    Token can be a symbol (e.g. 'ETH') or a contract address.
    Returns None if price lookup fails.
    """
    key = (token.lower(), timestamp)
    if key in _price_cache:
        return _price_cache[key]

    iso_time = datetime.utcfromtimestamp(timestamp).isoformat() + "Z"
    headers = {
        "accept": "application/json",
        "X-Alchemy-Token": ALCHEMY_API_KEY,
    }
    payload = {
        "time": iso_time,
        "tokens": [token],
    }

    try:
        res = requests.post(BASE_URL, headers=headers, json=payload)
        res.raise_for_status()
        data = res.json()
        price = data.get("prices", [{}])[0].get("price")
        if price:
            _price_cache[key] = price
        return price
    except Exception as e:
        print(f"[price_cache] Failed price lookup for {token} at {timestamp}: {e}")
        return None
