"""
balances.py

Fetches the current token balances and USD values for a given Ethereum wallet
using Covalent's balances_v2 endpoint. Saves the result to a local JSON file
at /data/wallet_portfolio.json and includes the total current USD value.

Usage: Run as standalone script or import into ROI calculation pipeline.
"""

import os
import requests
import json
from dotenv import load_dotenv
from pathlib import Path

# Load API key from .env file
load_dotenv()
COVALENT_API_KEY = os.getenv("COVALENT_API_KEY")

# Constants
CHAIN_ID = "1"  # Ethereum Mainnet
ADDRESS = "0x0193138F52c349A66d0b7Ccbe29d70E613E6C968"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "wallet_portfolio.json"
API_URL = f"https://api.covalenthq.com/v1/{CHAIN_ID}/address/{ADDRESS}/balances_v2/"

def fetch_portfolio():
    """
    Calls Covalent API to fetch token balances and their USD values.
    Returns structured portfolio data or a mocked fallback on failure.
    """
    params = {
        "key": COVALENT_API_KEY,
        "nft": False,
        "no-nft-fetch": True,
    }

    try:
        response = requests.get(API_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        tokens = []
        total_value = 0.0

        for item in data.get("data", {}).get("items", []):
            balance = int(item.get("balance", 0)) / (10 ** item.get("contract_decimals", 0))
            value = item.get("quote", 0.0)  # already in USD
            if value and value > 0.01:  # Skip near-zero dust
                tokens.append({
                    "contract_name": item.get("contract_name"),
                    "contract_ticker_symbol": item.get("contract_ticker_symbol"),
                    "balance": round(balance, 6),
                    "quote": round(value, 2),
                })
                total_value += value

        return {
            "wallet": ADDRESS,
            "total_usd_value": round(total_value, 2),
            "tokens": sorted(tokens, key=lambda x: x["quote"], reverse=True),
        }

    except Exception as e:
        print(f"[ERROR] Failed to fetch portfolio: {e}")
        return {
            "wallet": ADDRESS,
            "total_usd_value": 0.0,
            "tokens": [],
            "note": "Mocked response due to API failure."
        }

def save_to_file(data):
    """
    Saves the given data dictionary as JSON to the OUTPUT_PATH.
    """
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[✅] Portfolio saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    portfolio = fetch_portfolio()
    save_to_file(portfolio)
