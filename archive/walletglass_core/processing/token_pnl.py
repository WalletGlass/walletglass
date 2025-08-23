"""
token_pnl.py

Calculates per-token realized and unrealized PnL for a given wallet address.

This module expects a normalized list of swap events, each with:
- token_symbol, token_address
- amount (positive float)
- direction ("buy" or "sell")
- timestamp (UNIX)
- pair_symbol (usually "ETH" or "USDC")

It uses historical ETH price lookups to estimate USD cost basis and sale proceeds.
Currently assumes all swaps are ETH-based for valuation purposes.

Used by: PnL engine, Streamlit frontend, AI summary generator.
"""

from collections import defaultdict
from decimal import Decimal
from walletglass_core.pricing.pricing_engine import get_price_at_time, fetch_current_eth_price
from walletglass_core.ingestion.etherscan import fetch_raw_eth_transactions
from walletglass_core.processing.parser import parse_swap_events

# 🔁 Replace stub with actual parser
from walletglass_core.processing.parser import parse_swap_events as fetch_swap_events


def calculate_token_pnl(wallet_address: str) -> dict:
    """
    Main function to calculate per-token PnL for a wallet.
    Returns a dict keyed by token symbol with metrics including:
    - realized/unrealized PnL
    - average buy/sell prices
    - total invested/proceeds
    """
    raw_txs = fetch_raw_eth_transactions(wallet_address)
    swap_events = parse_swap_events(raw_txs)

    print(f"🔄 Decoded {len(swap_events)} swap events")

    current_eth_price = fetch_current_eth_price()

    token_data = defaultdict(lambda: {
        "token_address": "",
        "total_acquired": Decimal("0"),
        "total_sold": Decimal("0"),
        "invested_usd": Decimal("0"),
        "proceeds_usd": Decimal("0"),
        "txs": []
    })

    for tx in swap_events:
        symbol = tx["token_symbol"]
        token_address = tx["token_address"]
        timestamp = tx["timestamp"]
        amount = Decimal(str(tx["amount"]))
        direction = tx["direction"]
        pair_symbol = tx.get("pair_symbol", "ETH")  # default fallback

        # For now we assume ETH-paired
        price_usd = get_price_at_time(timestamp)
        if price_usd is None or price_usd == Decimal("0.0"):
            if direction in ("buy", "sell"):
                print(f"[WARN] Missing price for {pair_symbol} at {timestamp}")
            continue


        token_data[symbol]["token_address"] = token_address

        if direction == "buy":
            token_data[symbol]["total_acquired"] += amount
            token_data[symbol]["invested_usd"] += amount * price_usd
        elif direction == "sell":
            token_data[symbol]["total_sold"] += amount
            token_data[symbol]["proceeds_usd"] += amount * price_usd

        token_data[symbol]["txs"].append(tx)

    results = {}
    for symbol, data in token_data.items():
        acquired = data["total_acquired"]
        sold = data["total_sold"]
        invested = data["invested_usd"]
        proceeds = data["proceeds_usd"]
        holding = acquired - sold
        realized_pnl = proceeds - invested
        unrealized_value = holding * current_eth_price
        net_pnl = realized_pnl + unrealized_value

        results[symbol] = {
            "symbol": symbol,
            "token_address": data["token_address"],
            "total_acquired": round(acquired, 4),
            "total_sold": round(sold, 4),
            "net_holding": round(holding, 4),
            "avg_buy_price_usd": round(invested / acquired, 8) if acquired > 0 else 0,
            "avg_sell_price_usd": round(proceeds / sold, 8) if sold > 0 else 0,
            "total_invested_usd": round(invested, 2),
            "total_proceeds_usd": round(proceeds, 2),
            "realized_pnl_usd": round(realized_pnl, 2),
            "unrealized_value_usd": round(unrealized_value, 2),
            "net_pnl_after_gas_usd": round(net_pnl, 2),  # placeholder; subtract gas later
        }

    return results
