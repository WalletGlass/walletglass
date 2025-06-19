from dataclasses import dataclass, field
from typing import List
from decimal import Decimal
from .transaction import Transaction


@dataclass
class Wallet:
    """A wallet with associated on-chain activity."""
    address: str
    transactions: List[Transaction] = field(default_factory=list)

    def total_gas_eth(self) -> Decimal:
        return sum(tx.gas_cost_eth() for tx in self.transactions)

    def funding_events(self) -> List[Transaction]:
        """Return transactions that are funding (e.g., large incoming transfers)."""
        return [tx for tx in self.transactions if tx.to_address.lower() == self.address.lower() and tx.value_eth > Decimal("0.01")]