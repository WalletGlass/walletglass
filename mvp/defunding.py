"""
defunding.py

Extracts all outbound ETH and ERC-20 transfers from a wallet,
labels them based on withdrawal destination (cex, bridge, eoa),
assigns USD value (with fallback), and saves two files:

- data/wallet_defunding_full.json (all outbound txs with status/reason)
- data/wallet_defunding.json (only accepted defunding txs)
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Any, List

# Load API keys
load_dotenv()
from mvp.secrets import get_secret
MORALIS_API_KEY  = get_secret("MORALIS_API_KEY")
ETHERSCAN_API_KEY = get_secret("ETHERSCAN_API_KEY")
HEADERS = {"X-API-Key": MORALIS_API_KEY}
BASE_URL = "https://deep-index.moralis.io/api/v2.2"
WALLET = "0x0193138F52c349A66d0b7Ccbe29d70E613E6C968".lower()

# Load fallback ETH price DB
with open("data/eth_price_db.json") as f:
    ETH_PRICE_DB = json.load(f)

# Load known withdrawal sinks
with open("data/known_withdrawal_sinks.json") as f:
    KNOWN_SINKS = json.load(f)


def _sum_defunded_usd(events: list) -> float:
    return round(sum(e.get("usd", 0.0) for e in events if e.get("status") == "accepted"), 2)


def fetch_transactions(wallet: str) -> list:
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


def label_defunding_sink(receiver: str) -> tuple[str, str]:
    receiver = receiver.lower()
    if receiver in KNOWN_SINKS:
        return "accepted", "known_sink"
    elif is_contract(receiver):
        return "rejected", "to_contract_not_in_registry"
    else:
        return "eoa", "to_eoa_not_in_registry"


def parse_eth(tx: dict, target_wallet: str) -> list:
    results = []
    for t in tx.get("native_transfers", []):
        from_addr = t.get("from_address", "").lower()
        to_addr = t.get("to_address", "").lower()
        if from_addr != target_wallet or to_addr == target_wallet:
            continue  # not outbound

        amount = float(t.get("value_formatted", 0))
        if amount < 0.01:
            continue

        date = tx["block_timestamp"][:10]
        usd_price = get_eth_usd_price(date)
        if usd_price is None:
            continue

        usd = round(usd_price * amount, 2)
        status, reason = label_defunding_sink(to_addr)

        results.append({
            "hash": tx["hash"],
            "block": int(tx["block_number"]),
            "timestamp": date,
            "token": "ETH",
            "to": to_addr,
            "amount": amount,
            "usd": usd,
            "status": status,
            "reason": reason
        })
    return results


def parse_erc20(tx: dict, target_wallet: str) -> list:
    results = []
    for t in tx.get("erc20_transfers", []):
        from_addr = t.get("from_address", "").lower()
        to_addr = t.get("to_address", "").lower()
        if from_addr != target_wallet or to_addr == target_wallet:
            continue

        symbol = t.get("token_symbol", "UNKNOWN")
        amount = float(t.get("value_formatted", 0))
        if amount < 1 or symbol == "UNKNOWN":
            continue

        try:
            usd = t.get("usd_value") or t.get("usdValue")
            if usd is not None:
                usd = float(usd)
            else:
                usd = float(tx.get("value", 0) or 0)

        except:
            continue

        status, reason = label_defunding_sink(to_addr)

        results.append({
            "hash": tx["hash"],
            "block": int(tx["block_number"]),
            "timestamp": tx["block_timestamp"][:10],
            "token": symbol,
            "to": to_addr,
            "amount": amount,
            "usd": round(usd, 2),
            "status": status,
            "reason": reason
        })
    return results


def get_defunding(address: str) -> Dict[str, Any]:
    target = address.lower()
    txs = fetch_transactions(target)

    all_events: List[dict] = []
    for tx in txs:
        all_events += parse_eth(tx, target)
        all_events += parse_erc20(tx, target)

    defunded_usd = _sum_defunded_usd(all_events)

    return {
        "defunded_usd": defunded_usd,
        "events": all_events
    }


def build_wallet_defunding():
    print("🔍 Fetching wallet transaction history...")
    txs = fetch_transactions(WALLET)

    all_events = []
    for tx in txs:
        all_events += parse_eth(tx, WALLET)
        all_events += parse_erc20(tx, WALLET)

    Path("data").mkdir(exist_ok=True)

    with open("data/wallet_defunding_full.json", "w") as f:
        json.dump(all_events, f, indent=2)

    filtered = [e for e in all_events if e["status"] == "accepted"]
    with open("data/wallet_defunding.json", "w") as f:
        json.dump(filtered, f, indent=2)

    print(f"✅ Saved {len(filtered)} accepted defunding events to wallet_defunding.json")
    print(f"🧾 Total outbound events logged: {len(all_events)}")


if __name__ == "__main__":
    build_wallet_defunding()
