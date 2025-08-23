# models/transaction.py

"""
Defines core data models used throughout WalletGlass:
- Transaction
- Token
- Wallet

These models are designed to be modular and easily extensible for multi-chain or multi-wallet support in the future.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime


@dataclass
class Token:
    """
    Represents an ERC20 token or native asset (e.g. ETH).
    """
    address: str  # Contract address (use "ETH" for native)
    symbol: str
    decimals: int


from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class Chain(str, Enum):
    ETH = "ethereum"
    BASE = "base"
    # future chains...

class TxType(str, Enum):
    SWAP = "swap"
    FUNDING = "funding"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    MINT = "mint"
    BURN = "burn"
    TRANSFER = "transfer"
    UNKNOWN = "unknown"

@dataclass
class TokenAmount:
    token_address: str
    token_symbol: str
    amount: float
    usd_value: Optional[float]

@dataclass
class Transaction:
    hash: str
    block_number: int
    timestamp: int
    chain: Chain
    from_address: str
    to_address: str
    tx_type: TxType
    protocol: Optional[str]
    method: Optional[str]
    gas_used_eth: float
    gas_cost_usd: Optional[float]
    inputs: List[TokenAmount]
    outputs: List[TokenAmount]
    comment: Optional[str] = None

@dataclass
class Wallet:
    """
    Placeholder for wallet metadata.
    Currently minimal, can support wallet type, labels, tags in future.
    """
    address: str

