"""
alchemy_adapter.py
──────────────────
Handles fetching raw transaction and log data from Alchemy using their JSON-RPC API.

Functions:
- fetch_transfers(address): Get all asset transfers for a wallet.
- fetch_tx_receipt(tx_hash): Get detailed logs for a specific transaction.
- fetch_txs_and_logs(address): Master function that returns both transfers and logs.

Requirements:
- Set ALCHEMY_API_KEY in your .env file

Usage:
- This module powers ingestion for WalletGlass, supplying raw input for decoding and parsing.
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Alchemy endpoint and key
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
if not ALCHEMY_API_KEY:
    raise ValueError("Missing ALCHEMY_API_KEY in environment.")

ALCHEMY_BASE_URL = "https://eth-mainnet.g.alchemy.com/v2"
ALCHEMY_URL = f"{ALCHEMY_BASE_URL}/{ALCHEMY_API_KEY}"  # This is the full URL we POST to


def fetch_transfers(address: str) -> list:
    """
    Fetch all ETH and token transfers involving the given address.
    Alchemy treats toAddress+fromAddress as AND filter — so we query separately and merge.
    """
    print(f"🔍 Fetching transfers for: {address}")

    def query(direction: str):
        key = "toAddress" if direction == "to" else "fromAddress"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "alchemy_getAssetTransfers",
            "params": [{
                "fromBlock": "0x0",
                "toBlock": "latest",
                "withMetadata": True,
                "excludeZeroValue": False,
                "maxCount": "0x3e8",
                "category": ["external", "erc20", "erc721"],
                key: address
            }]
        }
        response = requests.post(ALCHEMY_URL, json=payload)
        response.raise_for_status()
        result = response.json().get("result", {})
        return result.get("transfers", [])

    # Fetch both incoming and outgoing separately
    to_transfers = query("to")
    from_transfers = query("from")

    combined = to_transfers + from_transfers
    print(f"✅ Fetched {len(combined)} transfers (🔼{len(from_transfers)} out, 🔽{len(to_transfers)} in)")
    return combined



def fetch_tx_receipt(tx_hash: str) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_getTransactionReceipt",
        "params": [tx_hash]
    }
    response = requests.post(ALCHEMY_URL, json=payload)
    response.raise_for_status()
    data = response.json()

    # DEBUGGING HERE 👇
    print(f"🔍 Receipt for {tx_hash[:10]}...: ", "logs" in data.get("result", {}))

    return data["result"]



def fetch_txs_and_logs(address: str) -> list:
    print(f"🔍 Fetching transfers for: {address}")
    transfers = fetch_transfers(address)
    print(f"✅ Fetched {len(transfers)} transfers (🔼{sum(1 for t in transfers if t['category'] == 'external' and t['from'].lower() == address.lower())} out, 🔽{sum(1 for t in transfers if t['to'].lower() == address.lower())} in)")

    results = []

    for transfer in transfers:
        tx_hash = transfer["hash"]
        try:
            receipt = fetch_tx_receipt(tx_hash)

            result = {
                "tx_hash": tx_hash,
                "from": transfer.get("from"),
                "to": transfer.get("to"),
                "value": transfer.get("value"),
                "asset": transfer.get("asset"),
                "category": transfer.get("category"),
                "timestamp": transfer.get("metadata", {}).get("blockTimestamp"),
                "logs": receipt.get("logs", []),
            }

            results.append(result)

        except Exception as e:
            print(f"⚠️ Error fetching logs for {tx_hash[:10]}...: {e}")

    print(f"🧾 Retrieved logs for {len(results)} transactions")
    print(f"🧪 Raw logs retrieved: {sum(len(tx['logs']) for tx in results)}")
    return results
