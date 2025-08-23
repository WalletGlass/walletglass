"""
dump_transfers.py

Simple script to fetch raw inbound transfers via Alchemy and save to JSON.
Use this to inspect the Alchemy input structure before decoding logic.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
ALCHEMY_URL = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

WALLET_ADDRESS = "0x0193138F52c349A66d0b7Ccbe29d70E613E6C968"


def fetch_transfers(wallet: str) -> list:
    """
    Fetch all inbound ETH + ERC20 transfers using Alchemy.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "alchemy_getAssetTransfers",
        "params": [{
            "fromBlock": "0x0",
            "toAddress": wallet,
            "category": ["external", "erc20"],
            "withMetadata": True,
            "excludeZeroValue": True,
            "maxCount": "0x3e8",  # 1000
            "order": "asc"
        }]
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(ALCHEMY_URL, headers=headers, json=payload)
    data = response.json()

    return data.get("result", [])


def main():
    transfers = fetch_transfers(WALLET_ADDRESS)

    os.makedirs("data", exist_ok=True)
    with open("data/raw_alchemy_transfers.json", "w") as f:
        json.dump(transfers, f, indent=2)

    print(f"✅ Saved {len(transfers)} raw transfers to data/raw_alchemy_transfers.json")

    if isinstance(transfers, list) and transfers:
        print("\n🔍 First 3 transfers:\n")
        for tx in transfers[:3]:
            print(json.dumps(tx, indent=2))
            print("\n" + "-" * 60 + "\n")
    else:
        print("⚠️ No valid transfers found or response not a list. Check raw_alchemy_transfers.json.")

if __name__ == "__main__":
    main()
