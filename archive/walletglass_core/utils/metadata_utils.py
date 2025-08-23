# 🏷️ metadata_utils.py — Token metadata lookup utility
"""
Loads token symbol and decimals from a local JSON cache.
Fallback support can be added later using on-chain Alchemy calls.
"""

import json
import os

# Assumes file is stored at walletglass_core/data/token_metadata.json
TOKEN_METADATA_PATH = os.path.join(os.path.dirname(__file__), '../data/token_metadata.json')

# -----------------------------
# 🔎 Load Metadata from JSON
# -----------------------------
def load_token_metadata():
    try:
        with open(TOKEN_METADATA_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load token metadata: {e}")
        return {}

# -----------------------------
# 🔖 Resolve Metadata by Address
# -----------------------------
def resolve_token_metadata(address):
    metadata = load_token_metadata()
    entry = metadata.get(address.lower())
    if entry:
        return {
            "symbol": entry.get("symbol", "UNKNOWN"),
            "decimals": entry.get("decimals", 18)
        }
    return {
        "symbol": "UNKNOWN",
        "decimals": 18
    }
