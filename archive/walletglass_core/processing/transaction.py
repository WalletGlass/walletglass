from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from datetime import datetime

@dataclass
class Transaction:
    """Base class for a blockchain transaction."""
    tx_hash: str
    timestamp: datetime
    from_address: str
    to_address: str
    value_eth: Decimal  # Raw ETH value (if native transfer)
    gas_used: int
    gas_price_gwei: Decimal
    token_symbol: Optional[str] = None
    token_amount: Optional[Decimal] = None
    token_address: Optional[str] = None
    tx_type: Optional[str] = None  # e.g. 'swap', 'send', 'receive'

    def gas_cost_eth(self) -> Decimal:
        """Calculate total gas cost in ETH."""
        return Decimal(self.gas_used) * self.gas_price_gwei / Decimal(1_000_000_000)