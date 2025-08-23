"""
uniswap_v2.py

Handles identification and decoding of Uniswap V2 swap transactions.

Currently uses placeholder logic that always returns dummy token swap data 
if the method signature matches a known Uniswap V2 method ID.

To be replaced with real decoding logic in future iterations.
"""

# Known Uniswap V2 method IDs
UNISWAP_V2_METHODS = {
    "0x38ed1739": "swapExactTokensForTokens",
    "0x18cbafe5": "swapExactETHForTokens",
    "0x7ff36ab5": "swapExactETHForTokensSupportingFeeOnTransferTokens",
    "0x5c11d795": "swapTokensForExactETH",
}

def is_uniswap_v2_swap(input_data: str) -> bool:
    """
    Checks if a transaction input matches a known Uniswap V2 swap method ID.

    Args:
        input_data (str): The transaction input field (hex string)

    Returns:
        bool: True if it matches a known Uniswap V2 swap method
    """
    return input_data[:10] in UNISWAP_V2_METHODS

def parse_uniswap_v2_swap(tx: dict) -> dict:
    """
    Dummy parser for Uniswap V2 swaps.

    Args:
        tx (dict): Raw transaction dictionary from Etherscan

    Returns:
        dict: Standardized swap event data
    """
    return {
        "token_symbol": "V2TOKEN",
        "token_address": "0x000000000000000000000000000000000000v2",
        "amount": 123.45,
        "timestamp": int(tx["timeStamp"]),
        "direction": "buy",
        "tx_hash": tx["hash"],
        "pair_symbol": "ETH"
    }

