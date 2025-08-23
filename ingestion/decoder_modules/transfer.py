"""
ERC Transfer Decoder
--------------------
Handles decoding of ERC20, ERC721, and ERC1155 Transfer events.
"""

from typing import Optional, Dict, Any

def decode_transfer(log: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Decodes a Transfer event from log. Returns normalized dict or None.
    Expected topic0 (ERC20/721): Transfer(address,address,uint256)
    """
    try:
        topics = log.get("topics", [])
        if len(topics) != 3:
            return None  # Not a standard Transfer event

        from_address = "0x" + topics[1][-40:]
        to_address = "0x" + topics[2][-40:]
        token_address = log.get("address")
        value_hex = log.get("data", "0x0")
        value = int(value_hex, 16)

        return {
            "event": "transfer",
            "token_address": token_address,
            "from": from_address,
            "to": to_address,
            "amount": value,
            "tx_hash": log.get("transactionHash"),
            "block_number": int(log.get("blockNumber", "0x0"), 16)
        }

    except Exception as e:
        print(f"❌ Failed to decode Transfer: {e}")
        return None
