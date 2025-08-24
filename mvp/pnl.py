"""
pnl.py — Compare funded USD vs current wallet value and calculate ROI.

Reads (for CLI/debug):
- /data/wallet_funding.json → contains total_funded_usd (or list of events)
- /data/wallet_portfolio.json → contains total_usd_value

Outputs (for CLI/debug):
- Prints funded, current, ROI
- Saves result to /data/wallet_pnl.json

Also exposes a pure function for the UI:
- compute_pnl(funded_usd, current_value_usd) -> dict
"""

import json
from pathlib import Path
from typing import Dict, Any

# ---------- Constants ----------
FUNDING_PATH = Path("data/wallet_funding.json")
PORTFOLIO_PATH = Path("data/wallet_portfolio.json")
OUTPUT_PATH = Path("data/wallet_pnl.json")

# ---------- Helpers ----------

def load_json_file(filepath: Path) -> Any:
    """
    Load JSON or raise a clear error. (robust I/O)
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Missing file: {filepath}")
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise ValueError(f"Malformed JSON in file: {filepath}")

def save_json(data: Dict[str, Any], path: Path) -> None:
    """
    Save dict to JSON (pretty). (tiny utility)
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ---------- Pure PnL function (UI entrypoint) ----------

def compute_pnl(funded_usd: float, current_value_usd: float) -> Dict[str, float]:
    """
    Pure function (no file I/O, no prints):
    - funded_usd: total dollars funded into wallet
    - current_value_usd: current wallet value in dollars
    Returns rounded values + ROI%.

    *Divide-by-zero safe:* if funded_usd == 0 -> ROI = 0.0
    """
    funded = float(funded_usd or 0.0)
    current = float(current_value_usd or 0.0)
    net = current - funded
    roi = (net / funded * 100.0) if funded > 0 else 0.0

    return {
        "funded_usd": round(funded, 2),
        "current_value_usd": round(current, 2),
        "net_pnl_usd": round(net, 2),
        "roi_pct": round(roi, 2),
    }

# ---------- Adapter for your existing file-based flow ----------

def load_and_compute_from_files() -> Dict[str, float]:
    """
    Reads funding & portfolio JSONs, computes PnL using the pure function,
    and returns the same dict the UI uses.
    """
    funding_data = load_json_file(FUNDING_PATH)
    portfolio_data = load_json_file(PORTFOLIO_PATH)

    # Funding can be a summarized dict OR the raw accepted events list.
    if isinstance(funding_data, list):
        funded = sum(e.get("usd", 0.0) for e in funding_data if e.get("status") == "accepted")
    else:
        # prefer common keys
        funded = (
            funding_data.get("total_funded_usd") or
            funding_data.get("funded_usd") or
            0.0
        )

    current = (
        portfolio_data.get("total_usd_value") or
        portfolio_data.get("current_value_usd") or
        0.0
    )

    if funded is None or current is None:
        raise ValueError("Missing keys in input JSON files.")

    return compute_pnl(funded, current)

# ---------- CLI (kept for local debugging) ----------

def main() -> None:
    try:
        pnl = load_and_compute_from_files()

        # CLI Output
        print(f"Funded: ${pnl['funded_usd']}")
        print(f"Current: ${pnl['current_value_usd']}")
        print(f"Net PnL: ${pnl['net_pnl_usd']}")
        print(f"ROI: {pnl['roi_pct']}%")

        # Save to output file for downstream scripts/tests
        save_json(pnl, OUTPUT_PATH)

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()
