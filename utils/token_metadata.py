# walletglass/core/token_metadata.py

"""
Helper for resolving token symbols and decimals from static metadata.
"""

import os
import json
import requests
# Load metadata once on import
TOKEN_METADATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "token_metadata.json")
with open(TOKEN_METADATA_PATH, "r") as f:
    _TOKEN_MAP = json.load(f)

import requests

def get_token_info(address: str):
    """
    Resolves token metadata (symbol + decimals) from local or CoinGecko.

    Args:
        address (str): Ethereum token address (mixed or lowercase)

    Returns:
        dict: { symbol: str, decimals: int }
    """
    address = address.lower()

    # Try local JSON
    token = _TOKEN_MAP.get(address)
    if token:
        return token

    # Try CoinGecko
    try:
        url = f"https://api.coingecko.com/api/v3/coins/ethereum/contract/{address}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "symbol": data["symbol"].upper(),
                "decimals": data.get("detail_platforms", {}).get("ethereum", {}).get("decimals", 18)
            }
    except Exception as e:
        print(f"[⚠️] CoinGecko fallback failed for {address}: {e}")

    # Fallback if all else fails
    return {
        "symbol": address[:6] + "...",
        "decimals": 18
    }
