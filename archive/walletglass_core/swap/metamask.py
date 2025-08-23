"""
MetaMask Swaps Parser (Stub)
Detects and flags swaps routed through MetaMask’s aggregator contract.
Future versions will parse logs to extract actual swap details.
"""

from typing import Dict, Any

# MetaMask Swaps contract address (mainnet)
METAMASK_ROUTER = "0x881d40237659c251811cec9c364ef91dc08d300c".lower()


def is_metamask_swap(tx: Dict[str, Any]) -> bool:
    """
    Detect if the transaction is routed through MetaMask's swap contract.
    
    Args:
        tx: A transaction dictionary from Etherscan API.
        
    Returns:
        True if it's a MetaMask swap, False otherwise.
    """
    to_address = tx.get("to", "").lower()
    return to_address == METAMASK_ROUTER


def parse_metamask_swap(tx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder parser for MetaMask swaps.
    
    Args:
        tx: A transaction dictionary from Etherscan API.
        
    Returns:
        A placeholder parsed swap dictionary.
    """
    return {
        "protocol": "MetaMask",
        "hash": tx.get("hash"),
        "token_in": "UNKNOWN",
        "token_out": "UNKNOWN",
        "amount_in": None,
        "amount_out": None,
        "timestamp": int(tx.get("timeStamp", 0)),
    }
