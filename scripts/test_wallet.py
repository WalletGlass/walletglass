import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.core.ingestor import load_wallet_transactions
from packages.core.wallet import Wallet
from decimal import Decimal
from rich import print

WALLET_ADDRESS = "0xc0ffee254729296a45a3885639ac7e10f9d54979"

def main():
    print(f"[bold cyan]Loading wallet:[/bold cyan] {WALLET_ADDRESS}")
    
    txs = load_wallet_transactions(WALLET_ADDRESS)
    wallet = Wallet(address=WALLET_ADDRESS, transactions=txs)

    print(f"\n[bold green]Transactions ({len(wallet.transactions)} total):[/bold green]")
    for tx in wallet.transactions:
        print(f"- [{tx.tx_type.upper()}] {tx.value_eth} ETH from {tx.from_address[:6]}... to {tx.to_address[:6]}...")

    gas_total = wallet.total_gas_eth()
    print(f"\n[bold magenta]Total gas used:[/bold magenta] {gas_total:.6f} ETH")

if __name__ == "__main__":
    main()
