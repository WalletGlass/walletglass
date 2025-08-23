# pnl_test.py

import sys
import os
from decimal import Decimal

# 🔧 Fix path to ensure 'packages' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rich import print
from walletglass_core.ingestion.etherscan import fetch_eth_transactions
from walletglass_core.processing.wallet import Wallet
from walletglass_core.ingestion.filters import filter_small_transfers
from walletglass_core.processing.pnl import calculate_eth_pnl, fetch_current_eth_price

WALLET_ADDRESS = "0xc0ffee254729296a45a3885639ac7e10f9d54979"

def main():
    print(f"[bold cyan]Analyzing ETH PnL for:[/bold cyan] {WALLET_ADDRESS}\n")

    txs = fetch_eth_transactions(WALLET_ADDRESS)
    txs = filter_small_transfers(txs)

    print("[bold blue]ETH PnL uses historical prices per transaction[/bold blue]")

    # Calculate PnL using historical prices
    summary = calculate_eth_pnl(txs, WALLET_ADDRESS, Decimal("0.0"))

    # Fetch current ETH price for comparison
    current_price = fetch_current_eth_price()
    current_basis = summary["received"] * current_price

    print("\n[bold green]ETH Summary:[/bold green]")
    print(f"- Total Received:           {summary['received']} ETH")
    print(f"- Total Sent:               {summary['sent']} ETH")
    print(f"- Cost Basis (Historical):  ${summary['cost_basis']}")
    print(f"- Realized PnL:             ${summary['realized_profit']}")
    print(f"- Cost Basis @ Today’s Price: ${current_basis.quantize(Decimal('0.01'))} (for reference only)")

if __name__ == "__main__":
    main()
