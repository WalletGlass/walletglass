"""
Build Transaction objects from normalized decoded events.

Each function converts a specific event type (transfer, swap, etc.) into
a fully structured `Transaction` instance used by WalletGlass.
"""

from typing import Dict, Any, Optional
from models.transaction import Transaction


def build_transaction_from_transfer(event: Dict[str, Any]) -> Optional[Transaction]:
    """
    Convert a decoded ERC20/ERC721 transfer event into a Transaction object.

    Args:
        event (dict): Decoded transfer event from decoder_transfer.py

    Returns:
        Transaction or None
    """
    try:
        return Transaction(
            tx_hash=event.get("tx_hash"),
            block_number=event.get("block_number"),
            timestamp=event.get("timestamp"),
            protocol="erc20_transfer",  # can be updated with metadata later
            method="transfer",
            sender=event.get("from"),
            receiver=event.get("to"),
            token_address=event.get("contract"),
            amount=event.get("amount"),
            token_symbol=event.get("symbol", "?"),
            usd_price=event.get("usd_price", None),
            usd_value=event.get("usd_value", None),
            direction=event.get("direction", "unknown"),
            gas_used=event.get("gas_used", None),
            gas_price=event.get("gas_price", None),
        )
    except Exception as e:
        print(f"❌ Failed to build transfer transaction: {e}")
        return None


def build_transaction_from_uniswap_v3(event: Dict[str, Any]) -> Optional[Transaction]:
    """
    Convert a decoded Uniswap V3 Swap event into a Transaction object.

    Args:
        event (dict): Decoded swap event from decoder_uniswap_v3.py

    Returns:
        Transaction or None
    """
    try:
        return Transaction(
            tx_hash=event.get("tx_hash"),
            block_number=event.get("block_number"),
            timestamp=event.get("timestamp"),
            protocol="uniswap_v3",
            method="swap",
            sender=event.get("from"),
            receiver=event.get("to"),
            token_address=event.get("contract"),
            amount=event.get("amount_in"),
            token_symbol=None,  # To be enriched in metadata phase
            usd_price=None,
            usd_value=None,
            direction=event.get("direction"),
            gas_used=None,
            gas_price=None,
        )
    except Exception as e:
        print(f"❌ Failed to build Uniswap V3 transaction: {e}")
        return None
