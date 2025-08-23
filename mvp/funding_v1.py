"""
funding.py

Extracts all inbound ETH and ERC-20 transfers to a wallet,
labels them based on funding source (cex, bridge, eoa),
assigns USD value (with fallback), and saves two files:

- data/wallet_funding_full.json (all inbound txs with status/reason)
- data/wallet_funding.json (only accepted funding txs)
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load API keys
load_dotenv()
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
BASE_URL = "https://deep-index.moralis.io/api/v2.2"
HEADERS = {"x-api-key": MORALIS_API_KEY}
WALLET = "0x0193138F52c349A66d0b7Ccbe29d70E613E6C968".lower()

# Load fallback ETH price DB
with open("data/eth_price_db.json") as f:
    ETH_PRICE_DB = json.load(f)

# Load known funding sources
with open("data/known_funding_sources.json") as f:
    KNOWN_SOURCES = json.load(f)


def fetch_transactions(wallet: str) -> list:
    """
    Fetch all wallet transactions (ETH + ERC20) from Moralis
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


def is_contract(address: str) -> bool:
    """
    Check if address is a smart contract using Etherscan
    """
    url = "https://api.etherscan.io/api"
    params = {
        "module": "contract",
        "action": "getsourcecode",
        "address": address,
        "apikey": ETHERSCAN_API_KEY
    }
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code != 200:
            return False
        data = res.json()
        result = data.get("result")
        if not isinstance(result, list) or len(result) == 0:
            return False
        abi = result[0].get("ABI", "")
        return abi not in ["", "Contract source code not verified"]
    except Exception as e:
        print(f"⚠️ Etherscan error for {address}: {e}")
        return False


def get_eth_usd_price(date: str) -> float | None:
    return ETH_PRICE_DB.get(date)


def label_funding_source(sender: str) -> tuple[str, str]:
    """
    Returns: status, reason
    """
    sender = sender.lower()
    if sender in KNOWN_SOURCES:
        return "accepted", "known_source"
    elif is_contract(sender):
        return "rejected", "from_contract_not_in_registry"
    else:
        return "eoa", "from_eoa_not_in_registry"


def parse_eth(tx: dict) -> list:
    results = []
    for t in tx.get("native_transfers", []):
        to_addr = t.get("to_address", "").lower()
        from_addr = t.get("from_address", "").lower()
        if to_addr != WALLET or from_addr == WALLET:
            continue

        amount = float(t.get("value_formatted", 0))
        if amount < 0.01:
            continue

        date = tx["block_timestamp"][:10]
        usd_price = get_eth_usd_price(date)
        if usd_price is None:
            continue

        usd = round(usd_price * amount, 2)
        status, reason = label_funding_source(from_addr)

        results.append({
            "hash": tx["hash"],
            "block": int(tx["block_number"]),
            "timestamp": date,
            "token": "ETH",
            "from": from_addr,
            "amount": amount,
            "usd": usd,
            "status": status,
            "reason": reason
        })
    return results


def parse_erc20(tx: dict) -> list:
    results = []
    for t in tx.get("erc20_transfers", []):
        to_addr = t.get("to_address", "").lower()
        from_addr = t.get("from_address", "").lower()
        if to_addr != WALLET or from_addr == WALLET:
            continue

        symbol = t.get("token_symbol", "UNKNOWN")
        amount = float(t.get("value_formatted", 0))
        if amount < 1 or symbol == "UNKNOWN":
            continue

        try:
            usd = float(tx.get("value", 0))
            if usd <= 0 or usd > 1_000_000:
                continue
        except:
            continue

        status, reason = label_funding_source(from_addr)

        results.append({
            "hash": tx["hash"],
            "block": int(tx["block_number"]),
            "timestamp": tx["block_timestamp"][:10],
            "token": symbol,
            "from": from_addr,
            "amount": amount,
            "usd": round(usd, 2),
            "status": status,
            "reason": reason
        })
    return results


def build_wallet_funding():
    print("🔍 Fetching wallet transaction history...")
    txs = fetch_transactions(WALLET)

    all_events = []
    for tx in txs:
        all_events += parse_eth(tx)
        all_events += parse_erc20(tx)

    Path("data").mkdir(exist_ok=True)

    # Save full log
    with open("data/wallet_funding_full.json", "w") as f:
        json.dump(all_events, f, indent=2)

    # Save only accepted entries
    filtered = [e for e in all_events if e["status"] == "accepted"]
    with open("data/wallet_funding.json", "w") as f:
        json.dump(filtered, f, indent=2)

    print(f"✅ Saved {len(filtered)} accepted funding events to wallet_funding.json")
    print(f"🧾 Total inbound events logged: {len(all_events)}")


if __name__ == "__main__":
    build_wallet_funding()
