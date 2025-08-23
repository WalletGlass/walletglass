# 🧱 models.py — Shared data models for WalletGlass parsing pipeline
"""
Defines structured classes for parsed transaction data.
These models are used throughout the pipeline to ensure consistency,
easy formatting, and integration with analytics (PnL, funding, etc).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class TokenTransfer:
    token: str  # Symbol, e.g. ETH, USDC
    amount: float
    from_addr: str
    to_addr: str

@dataclass
class InternalTransfer:
    value_eth: float
    from_addr: str
    to_addr: str

@dataclass
class GasInfo:
    gas_used: int
    gas_price_wei: int
    eth_spent: float  # Derived from used * price

@dataclass
class ParsedTx:
    hash: str
    protocol: str  # e.g. Uniswap, 1inch, etc.
    type: str      # swap, fund, withdraw, transfer, unknown
    tokens: List[str] = field(default_factory=list)
    amounts: List[float] = field(default_factory=list)
    transfers: List[TokenTransfer] = field(default_factory=list)
    internals: List[InternalTransfer] = field(default_factory=list)
    gas: Optional[GasInfo] = None
    timestamp: Optional[int] = None
    raw: Dict = field(default_factory=dict)  # Full original tx for reference

    def summary(self):
        return {
            "hash": self.hash[:10] + "...",
            "protocol": self.protocol,
            "type": self.type,
            "tokens": self.tokens,
            "amounts": self.amounts,
            "eth_gas": self.gas.eth_spent if self.gas else None
        }
