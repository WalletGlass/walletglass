"""
pnl.py — Net-funded ROI calculator for WalletGlass MVP.

Reads (file-based debug/CLI):
- data/wallet_funding.json    → total_funded_usd OR list of accepted events
- data/wallet_defunding.json  → total_defunded_usd OR list of accepted events (optional)
- data/wallet_portfolio.json  → total_usd_value

Outputs:
- Prints funded/defunded/net-funded/current/net-PnL/ROI
- Saves JSON to data/wallet_pnl.json

Exposes pure function for UI/tests:
- compute_pnl(funded_usd, defunded_usd, current_value_usd) -> dict
"""

import json
from pathlib import Path
from typing import Any, Dict

# ---------- Paths ----------
FUNDING_PATH   = Path("data/wallet_funding.json")
DEFUNDING_PATH = Path("data/wallet_defunding.json")  # optional
PORTFOLIO_PATH = Path("data/wallet_portfolio.json")
OUTPUT_PATH    = Path("data/wallet_pnl.json")


# ---------- Small I/O utils ----------

def load_json_file(path: Path) -> Any:
    """
    Load JSON with clear errors.
    """
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in file: {path}: {e}") from e


def save_json(data: Dict[str, Any], path: Path) -> None:
    """
    Save dict to JSON (pretty).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ---------- Format adapters (robust to shapes) ----------

def _extract_total_funded_usd(obj: Any) -> float:
    """
    Supports either:
      - list of events with {"usd": float, "status": "accepted"}
      - dict with {"total_funded_usd": float} or {"funded_usd": float}
    """
    if isinstance(obj, list):
        return float(sum(e.get("usd", 0.0) for e in obj if e.get("status") == "accepted"))
    if isinstance(obj, dict):
        return float(obj.get("total_funded_usd") or obj.get("funded_usd") or 0.0)
    raise ValueError("Unexpected funding JSON shape (must be list or dict).")


def _extract_total_defunded_usd(obj: Any) -> float:
    """
    Supports either:
      - list of events with {"usd": float, "status": "accepted"}
      - dict with {"total_defunded_usd": float} or {"defunded_usd": float}
    """
    if isinstance(obj, list):
        return float(sum(e.get("usd", 0.0) for e in obj if e.get("status") == "accepted"))
    if isinstance(obj, dict):
        return float(obj.get("total_defunded_usd") or obj.get("defunded_usd") or 0.0)
    raise ValueError("Unexpected defunding JSON shape (must be list or dict).")


def _extract_current_usd_value(obj: Any) -> float:
    """
    Supports either:
      - dict with {"total_usd_value": float} (preferred)
      - dict with {"current_value_usd": float} (fallback)
      - list of tokens with {"usd_value": float} (fallback)
    """
    if isinstance(obj, dict):
        val = obj.get("total_usd_value")
        if val is None:
            val = obj.get("current_value_usd")
        if val is not None:
            return float(val)
    if isinstance(obj, list):
        return float(sum(t.get("usd_value", 0.0) for t in obj))
    raise ValueError("Unexpected portfolio JSON shape (must be dict or list).")


# ---------- Pure PnL core (UI/tests call this) ----------

def compute_pnl(
    funded_usd: float,
    defunded_usd: float,
    current_value_usd: float
) -> Dict[str, float]:
    """
    Pure function (no file I/O).
    Definitions:
      net_funded_usd = funded_usd - defunded_usd
      net_pnl_usd    = current_value_usd - net_funded_usd
      roi_pct        = 0.0 if net_funded_usd <= 0 else (net_pnl_usd / net_funded_usd) * 100

    Returns rounded values.
    """
    funded   = float(funded_usd or 0.0)
    defunded = float(defunded_usd or 0.0)
    current  = float(current_value_usd or 0.0)

    net_funded = funded - defunded
    net_pnl = current - net_funded

    if net_funded > 0:
        roi = (net_pnl / net_funded) * 100.0
    else:
        # If you've fully withdrawn or more, ROI on a non-positive cost basis is undefined.
        # We return 0.0 to avoid noisy infinities and keep UI stable.
        roi = 0.0

    return {
        "funded_usd": round(funded, 2),
        "defunded_usd": round(defunded, 2),
        "net_funded_usd": round(net_funded, 2),
        "current_value_usd": round(current, 2),
        "net_pnl_usd": round(net_pnl, 2),
        "roi_pct": round(roi, 2),
    }


# ---------- File-based adapter for local runs/CLI ----------

def load_and_compute_from_files() -> Dict[str, float]:
    """
    Reads the three JSONs, adapts shapes, and computes PnL.
    defunding file is optional; if missing, treated as 0.
    """
    funding_raw = load_json_file(FUNDING_PATH)
    portfolio_raw = load_json_file(PORTFOLIO_PATH)

    funded = _extract_total_funded_usd(funding_raw)
    current = _extract_current_usd_value(portfolio_raw)

    # defunding is optional for now
    if DEFUNDING_PATH.exists():
        defunding_raw = load_json_file(DEFUNDING_PATH)
        defunded = _extract_total_defunded_usd(defunding_raw)
    else:
        defunded = 0.0

    return compute_pnl(funded, defunded, current)


# ---------- CLI ----------

def main() -> None:
    try:
        pnl = load_and_compute_from_files()

        # CLI Output (readable, consistent)
        print(f"Funded: ${pnl['funded_usd']}")
        if pnl["defunded_usd"] > 0:
            print(f"Defunded: ${pnl['defunded_usd']}")
            print(f"Net Funded: ${pnl['net_funded_usd']}")
        print(f"Current: ${pnl['current_value_usd']}")
        print(f"Net PnL: ${pnl['net_pnl_usd']}")
        print(f"ROI: {pnl['roi_pct']}%")

        # Persist for downstream UI/tests
        save_json(pnl, OUTPUT_PATH)

    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
