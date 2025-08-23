"""
pnl.py — Compare funded USD vs current wallet value and calculate ROI.

Reads:
- /data/wallet_funding.json → contains total_funded_usd
- /data/wallet_portfolio.json → contains current_usd_value

Outputs:
- Prints funded, current, ROI
- Saves result to /data/wallet_pnl.json

Author: WalletGlass Core
"""

import json
import os
from pathlib import Path

# ---------- Constants ----------
FUNDING_PATH = Path("data/wallet_funding.json")
PORTFOLIO_PATH = Path("data/wallet_portfolio.json")
OUTPUT_PATH = Path("data/wallet_pnl.json")

# ---------- Helpers ----------

def load_json_file(filepath):
    """
    Loads a JSON file and returns its content.
    Raises an exception if file is missing or malformed.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Missing file: {filepath}")
    
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise ValueError(f"Malformed JSON in file: {filepath}")

def compute_roi(funded, current):
    """
    Computes net gain/loss and ROI percentage.
    Returns a dictionary with the result.
    """
    gain_loss = current - funded
    roi_pct = (gain_loss / funded) * 100 if funded != 0 else 0
    return {
        "funded_usd": round(funded, 2),
        "current_usd": round(current, 2),
        "roi_pct": round(roi_pct, 2),
        "net_gain_loss": round(gain_loss, 2)
    }

def save_json(data, path):
    """
    Saves dictionary data to a JSON file.
    """
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ---------- Main ----------

def main():
    try:
        funding_data = load_json_file(FUNDING_PATH)
        portfolio_data = load_json_file(PORTFOLIO_PATH)

        # Support both summarized and raw formats
        if isinstance(funding_data, list):
            funded = sum(e["usd"] for e in funding_data if e.get("status") == "accepted")
        else:
            funded = funding_data.get("total_funded_usd")

        current = portfolio_data.get("total_usd_value")

        if funded is None or current is None:
            raise ValueError("Missing keys in input JSON files.")

        roi_data = compute_roi(funded, current)

        # CLI Output
        print(f"Funded: ${roi_data['funded_usd']}")
        print(f"Current: ${roi_data['current_usd']}")
        print(f"ROI: {roi_data['roi_pct']}%")

        # Save to output file
        save_json(roi_data, OUTPUT_PATH)

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()
