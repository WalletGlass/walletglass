from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional


@dataclass
class Swap:
    """Represents a token-to-token swap on-chain."""
    tx_hash: str
    timestamp: datetime
    token_in: str
    amount_in: Decimal
    token_out: str
    amount_out: Decimal
    platform: str  # e.g. 'Uniswap', 'Sushi'

    def price_impact(self) -> Optional[float]:
        """Placeholder for calculating swap slippage or efficiency."""
        return None
