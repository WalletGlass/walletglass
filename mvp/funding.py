"""
funding.py

Extracts all inbound funding events (ETH and ERC-20 tokens)
for a wallet using Moralis API. Assigns USD value at the
time of transfer (fallback if needed) and saves clean,
sanity-checked data to data/wallet_funding.json
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load Moralis API key from .env
load_dotenv()
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
BASE_URL = "https://deep-index.moralis.io/api/v2.2"
HEADERS = {"x-api-key": MORALIS_API_KEY}

# Target wallet
WALLET = "0x0193138F52c349A66d0b7Ccbe29d70E613E6C968".lower()

# Load fallback ETH price DB
with open("data/eth_price_db.json") as f:
    ETH_PRICE_DB = json.load(f)


def fetch_all_transactions(wallet: str) -> list:
    """
    Fetch full wallet history from Moralis (native + erc20)
    """
    all_txs = []
    cursor = ""
    while True:
        url = f"{BASE_URL}/wallets/{wallet}/history"
        params = {"cursor": cursor, "exclude_spam": "true", "limit": 100}
        res = requests.get(url, headers=HEADERS, params=params)
        if res.status_code != 200:
            raise Exception(f"❌ Moralis fetch failed: {res.text}")
        data = res.json()
        all_txs += data.get("result", [])
        cursor = data.get("cursor")
        if not cursor or len(all_txs) >= 1000:
            break
    print(f"✅ Total transactions fetched: {len(all_txs)}")
    return all_txs


def get_eth_usd_price_fallback(date: str) -> float | None:
    """
    Returns fallback ETH price for a given date (YYYY-MM-DD)
    """
    return ETH_PRICE_DB.get(date)


def parse_eth_funding(tx: dict) -> list:
    """
    Extract inbound ETH transfers with USD value
    """
    funding = []
    for t in tx.get("native_transfers", []):
        from_addr = t.get("from_address", "").lower()
        to_addr = t.get("to_address", "").lower()
        if to_addr != WALLET or from_addr == WALLET:
            continue  # not inbound

        amount = float(t.get("value_formatted", 0))
        if amount < 0.01:
            continue  # ignore dust

        block = int(tx.get("block_number"))
        timestamp = tx.get("block_timestamp", "")
        date = timestamp[:10]  # YYYY-MM-DD

        price = get_eth_usd_price_fallback(date)
        if not price:
            print(f"[ETH skipped] No fallback price for {date}")
            continue

        usd = round(amount * price, 2)
        funding.append({
            "hash": tx["hash"],
            "block": block,
            "timestamp": date,
            "token": "ETH",
            "from": from_addr,
            "amount": amount,
            "usd": usd
        })
    return funding


def parse_erc20_funding(tx: dict) -> list:
    """
    Extract inbound ERC-20 transfers with sanity-checked USD values
    """
    funding = []
    for t in tx.get("erc20_transfers", []):
        from_addr = t.get("from_address", "").lower()
        to_addr = t.get("to_address", "").lower()
        if to_addr != WALLET or from_addr == WALLET:
            continue

        symbol = t.get("token_symbol", "UNKNOWN")
        amount = float(t.get("value_formatted", 0))
        if amount < 1 or not symbol or symbol == "UNKNOWN":
            continue

        try:
            usd = float(tx.get("value", 0))
            if usd <= 0 or usd > 1_000_000:
                continue  # sanity check
        except (TypeError, ValueError):
            continue

        funding.append({
            "hash": tx["hash"],
            "block": int(tx["block_number"]),
            "timestamp": tx["block_timestamp"][:10],
            "token": symbol,
            "from": from_addr,
            "amount": amount,
            "usd": round(usd, 2)
        })
    return funding


def build_wallet_funding():
    """
    Master runner function. Fetches, parses, filters and saves all funding events.
    """
    print("🔍 Fetching transaction history...")
    txs = fetch_all_transactions(WALLET)

    funding_events = []
    for tx in txs:
        funding_events += parse_eth_funding(tx)
        funding_events += parse_erc20_funding(tx)

    # Sort by block number
    funding_events = sorted(funding_events, key=lambda x: x["block"])

    Path("data").mkdir(exist_ok=True)
    with open("data/wallet_funding.json", "w") as f:
        json.dump(funding_events, f, indent=2)

    print(f"✅ {len(funding_events)} funding events saved to data/wallet_funding.json")


if __name__ == "__main__":
    build_wallet_funding()
