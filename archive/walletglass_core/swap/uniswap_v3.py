"""
uniswap_v3.py

Handles identification and decoding of Uniswap V3 swap transactions.

Currently uses placeholder logic that returns dummy swap data 
for any transaction matching a Uniswap V3 method signature.

Full ABI decoding will be added later using eth_abi.
"""

# Known Uniswap V3 method IDs
UNISWAP_V3_METHODS = {
    "0x414bf389": "exactInputSingle",
    "0xb858183f": "exactInput",
}

def is_uniswap_v3_swap(input_data: str) -> bool:
    """
    Checks if a transaction input matches a known Uniswap V3 swap method ID.

    Args:
        input_data (str): The transaction input field (hex string)

    Returns:
        bool: True if it matches a known Uniswap V3 method
    """
    return input_data[:10] in UNISWAP_V3_METHODS

def parse_uniswap_v3_swap(tx: dict) -> dict:
    """
    Dummy parser for Uniswap V3 swaps.

    Args:
        tx (dict): Raw transaction dictionary from Etherscan

    Returns:
        dict: Standardized swap event data
    """
    return {
        "token_symbol": "V3TOKEN",
        "token_address": "0x000000000000000000000000000000000000v3",
        "amount": 456.78,
        "timestamp": int(tx["timeStamp"]),
        "direction": "buy",
        "tx_hash": tx["hash"],
        "pair_symbol": "ETH"
    }
