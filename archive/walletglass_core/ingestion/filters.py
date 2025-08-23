from decimal import Decimal
from typing import List
from ..processing.transaction import Transaction
from ..constants import MIN_FUNDING_USD

def filter_small_transfers(transactions: List[Transaction], min_eth: Decimal = Decimal("0.005")) -> List[Transaction]:
    """Ignore ETH transfers below a certain threshold."""
    return [tx for tx in transactions if tx.value_eth >= min_eth]

def is_internal_transfer(tx: Transaction, wallet_address: str) -> bool:
    """Detect if the transaction is self-sent (from and to same wallet)."""
    return tx.from_address.lower() == wallet_address.lower() and tx.to_address.lower() == wallet_address.lower()

def detect_funding_events(transactions: List[Transaction], wallet_address: str, min_eth: Decimal = Decimal("0.01")) -> List[Transaction]:
    """Return large incoming transfers that might represent funding events."""
    return [
        tx for tx in transactions
        if tx.to_address.lower() == wallet_address.lower()
        and tx.value_eth >= min_eth
        and tx.from_address.lower() != wallet_address.lower()
    ]
