"""
balances_moralis.py

Robust Moralis (REST) portfolio fetch for WalletGlass MVP:
- Tries the modern "wallets/{address}/tokens" endpoint with price fields
- Falls back to legacy "{address}/erc20" endpoint with include=price
- Handles both response shapes (list vs. {result: [...]})
- Handles both casing styles (usd_value vs usdValue, balance_formatted vs balance/decimals)
- Ensures native ETH is present; fetches it separately if needed
- Fails loudly on HTTP errors; adds DEBUG mode for raw output

Outputs: /data/wallet_portfolio.json

Env:
  MORALIS_API_KEY=...
  WALLET_ADDRESS=0x...
  DEBUG_BALANCES=1       # optional, prints first 1-2 raw items

Author: WalletGlass (MVP v2)
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import requests
from dotenv import load_dotenv

# ---- Env & constants ----
load_dotenv()
API_KEY = os.getenv("MORALIS_API_KEY")
ADDRESS = os.getenv("WALLET_ADDRESS", "0x0193138F52c349A66d0b7Ccbe29d70E613E6C968")
CHAIN = "eth"
BASE_URL = "https://deep-index.moralis.io/api/v2.2"
HEADERS = {"X-API-Key": API_KEY}
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "wallet_portfolio.json"
DEBUG = os.getenv("DEBUG_BALANCES") in ("1", "true", "True")

# Moralis' pseudo-address for native ETH in some price endpoints
ETH_PSEUDO = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


# ---- HTTP helper with clear errors ----
def http_get(url: str, params: Dict[str, Any], timeout: int = 20) -> Dict[str, Any] | List[Dict[str, Any]]:
    resp = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
    if not resp.ok:
        raise RuntimeError(f"[❌] GET {url} failed: {resp.status_code} - {resp.text}")
    try:
        return resp.json()
    except Exception as e:
        raise RuntimeError(f"[❌] Non-JSON response from {url}: {e}")


# ---- Endpoint callers ----
def call_wallets_tokens(address: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Newer endpoint variant that can include price fields.
    We explicitly request USD price/value fields.
    """
    url = f"{BASE_URL}/wallets/{address}/tokens"
    params = {"chain": CHAIN, "include": "usd_price,usd_value"}
    data = http_get(url, params)

    # Shape can be a dict with "result" or sometimes a dict with pagination
    items = []
    if isinstance(data, dict):
        # common shapes: {"result":[...]} or {"cursor":"", "page":.., "result":[...]}
        items = data.get("result") or data.get("items") or []
    elif isinstance(data, list):
        items = data
    else:
        items = []

    return items, "wallets/{address}/tokens"


def call_erc20(address: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Legacy endpoint; include=price adds price fields if available.
    """
    url = f"{BASE_URL}/{address}/erc20"
    params = {"chain": CHAIN, "include": "price"}
    data = http_get(url, params)

    if isinstance(data, dict):
        items = data.get("result") or data.get("items") or []
    elif isinstance(data, list):
        items = data
    else:
        items = []

    return items, "{address}/erc20"


def get_native_eth_if_missing(address: str) -> Optional[Dict[str, Any]]:
    """
    If native ETH wasn't included in token list, fetch balance and price and return a token-like dict.
    Uses:
      - GET /{address}/balance             -> wei balance
      - GET /erc20/{ETH_PSEUDO}/price      -> usdPrice
    Returns None if anything fails (we don't hard-fail just for native top-up).
    """
    try:
        # balance
        bal_url = f"{BASE_URL}/{address}/balance"
        bal = http_get(bal_url, {"chain": CHAIN})
        balance_eth = int(bal.get("balance", 0)) / 1e18

        # price
        price_url = f"{BASE_URL}/erc20/{ETH_PSEUDO}/price"
        price = http_get(price_url, {"chain": CHAIN})
        usd_price = price.get("usdPrice") or price.get("usd_price") or 0.0

        usd_value = balance_eth * float(usd_price)
        return {
            "name": "Ether",
            "symbol": "ETH",
            "balance_formatted": str(balance_eth),
            "usd_value": usd_value,
            "native_token": True,
            "token_address": ETH_PSEUDO,
        }
    except Exception as e:
        # log but don't fail the whole run
        print(f"[warn] native ETH fetch fallback failed: {e}")
        return None


# ---- Parsing helpers ----
def as_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def normalize_item(token: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Convert a Moralis token item into WalletGlass token record:
      { contract_name, contract_ticker_symbol, balance, quote }
    Return None for dust (< $0.01) or unusable entries.
    """
    # price/value keys vary by endpoint/version
    usd_value = token.get("usd_value")
    if usd_value is None:
        usd_value = token.get("usdValue")
    if usd_value is None:
        usd_value = token.get("quote")
    usd_value = as_float(usd_value, 0.0)

    # skip dust
    if usd_value < 0.01:
        return None

    name = token.get("name") or "Unknown"
    symbol = token.get("symbol") or "UNK"

    # Prefer pre-formatted balance if present
    if "balance_formatted" in token and token["balance_formatted"] not in (None, ""):
        balance = as_float(token["balance_formatted"], 0.0)
    else:
        # compute from balance + decimals
        raw = token.get("balance")
        dec = token.get("decimals")
        try:
            raw_f = float(raw) if raw is not None else 0.0
            dec_i = int(dec) if dec is not None and str(dec).strip() != "" else 0
            balance = raw_f / (10 ** dec_i) if dec_i > 0 else raw_f
        except Exception:
            balance = 0.0

    return {
        "contract_name": name,
        "contract_ticker_symbol": symbol,
        "balance": round(balance, 6),
        "quote": round(usd_value, 2),
    }


def tokens_include_native(items: List[Dict[str, Any]]) -> bool:
    # native may be indicated by a flag or the pseudo address
    for t in items:
        if t.get("native_token") is True:
            return True
        addr = (t.get("token_address") or "").lower()
        if addr == ETH_PSEUDO.lower():
            return True
        # Some variants return ETH with empty decimals and ETH symbol; that's fine too.
    return False


# ---- Build portfolio ----
def fetch_all_tokens() -> Tuple[List[Dict[str, Any]], str]:
    """
    Try modern endpoint first; fall back to legacy.
    Return (items, endpoint_used).
    """
    try:
        items, src = call_wallets_tokens(ADDRESS)
        if items:
            return items, src
    except Exception as e:
        print(f"[info] wallets/tokens endpoint failed or empty: {e}")

    items, src = call_erc20(ADDRESS)
    return items, src


def build_portfolio() -> Dict[str, Any]:
    items, endpoint_used = fetch_all_tokens()

    if DEBUG:
        # Print just a peek of raw data for troubleshooting
        preview = items[:2] if isinstance(items, list) else items
        print("[debug] endpoint used:", endpoint_used)
        print("[debug] first items:", json.dumps(preview, indent=2, default=str))

    # Top up native ETH if missing
    if not tokens_include_native(items):
        native = get_native_eth_if_missing(ADDRESS)
        if native:
            items.append(native)

    tokens: List[Dict[str, Any]] = []
    total = 0.0
    for tok in items:
        norm = normalize_item(tok)
        if norm:
            tokens.append(norm)
            total += norm["quote"]

    tokens.sort(key=lambda x: x["quote"], reverse=True)

    return {
        "wallet": ADDRESS,
        "total_usd_value": round(total, 2),
        "tokens": tokens,
        "meta": {"source": "moralis", "endpoint": endpoint_used},
    }


def save_to_file(data: Dict[str, Any]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT_PATH.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    tmp.replace(OUTPUT_PATH)
    print(f"[✅] Portfolio saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    if not API_KEY:
        raise SystemExit("[❌] MORALIS_API_KEY missing in .env")
    portfolio = build_portfolio()
    save_to_file(portfolio)
    print(f"[📈] Total USD Value: ${portfolio['total_usd_value']} ({len(portfolio['tokens'])} tokens)")

