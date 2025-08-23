"""
utils.py

Shared decoding helpers used across swap modules like Uniswap V2, V3, etc.
Avoids circular imports by keeping decode_method_id and others here.
"""

from eth_abi.abi import decode as decode_abi
from eth_utils import function_signature_to_4byte_selector
import binascii


def decode_method_id(input_data: str) -> str:
    """
    Extract the 4-byte method selector from transaction input data.
    """
    if input_data.startswith("0x") and len(input_data) >= 10:
        return input_data[:10]
    return ""

def decode_token_amounts(input_data: str) -> dict:
    """
    Placeholder: Decodes token in/out amounts from transaction input data.
    Actual implementation depends on ABI format per method.
    """
    return {
        "token_in": None,
        "amount_in": None,
        "token_out": None,
        "amount_out": None
    }

def classify_token_symbols(tx_input: str) -> tuple[str, str]:
    """
    Placeholder: Assigns placeholder symbols to token pairs based on input.
    Will need ABI decoding to be real.
    """
    return ("TKN1", "TKN2")
