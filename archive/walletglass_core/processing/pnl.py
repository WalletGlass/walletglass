from decimal import Decimal
from typing import List, Dict
from .transaction import Transaction
from walletglass_core.pricing.pricing_engine import get_price_at_time, fetch_current_eth_price
from datetime import datetime

def calculate_eth_pnl(transactions: List[Transaction], wallet_address: str, placeholder_price: Decimal = Decimal("0.0")) -> Dict[str, Decimal]:
    """
    Calculate ETH received, sent, cost basis (historical), realized PnL,
    and compare to cost basis at today’s price.
    """
    received = Decimal("0.0")
    sent = Decimal("0.0")
    cost_basis = Decimal("0.0")
    realized_profit = Decimal("0.0")

    for tx in transactions:
        if tx.token_symbol and tx.token_symbol != "ETH":
            continue

        if tx.from_address.lower() == tx.to_address.lower():
            continue  # skip self transfers

        eth_price = get_price_at_time(int(tx.timestamp.timestamp()))

        if eth_price is None:
            print(f"[yellow]⚠ Skipping transaction at {tx.timestamp} — no price available[/yellow]")
            continue

        if tx.to_address.lower() == wallet_address.lower():
            received += tx.value_eth
            cost_basis += tx.value_eth * eth_price
        elif tx.from_address.lower() == wallet_address.lower():
            if received > 0:
                avg_cost = (cost_basis / received).quantize(Decimal("0.01"))
                realized_profit += (tx.value_eth * eth_price) - (tx.value_eth * avg_cost)
            sent += tx.value_eth

    # Fetch current ETH price for comparison
    current_eth_price = fetch_current_eth_price()
    current_cost_basis = received * current_eth_price
    unrealized_pnl = current_cost_basis - cost_basis

    return {
        "received": received,
        "sent": sent,
        "cost_basis": cost_basis.quantize(Decimal("0.01")),
        "realized_profit": realized_profit.quantize(Decimal("0.0001")),
        "current_cost_basis": current_cost_basis.quantize(Decimal("0.01")),
        "unrealized_pnl": unrealized_pnl.quantize(Decimal("0.01")),
        "eth_price_now": current_eth_price.quantize(Decimal("0.01")),
    }
