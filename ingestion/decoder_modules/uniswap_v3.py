"""
Uniswap V3 Swap decoder

This module decodes Swap events from Uniswap V3 pool contracts using log data.
"""

from typing import Dict, Any, Optional


def decode_uniswap_v3(log: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Decode a Uniswap V3 Swap event log into a normalized event dictionary.

    Args:
        log (dict): Raw log from Alchemy eth_getTransactionReceipt.

    Returns:
        dict or None: Normalized event if successful, None otherwise.
    """
    try:
        topics = log.get("topics", [])
        if len(topics) != 3:
            print(f"⛔ Skipping: Unexpected number of topics ({len(topics)})")
            return None

        sender = "0x" + topics[1][-40:]
        recipient = "0x" + topics[2][-40:]

        data = log.get("data", "")
        if not data or data == "0x":
            print(f"⛔ Skipping: No data field present in log")
            return None

        raw_bytes = bytes.fromhex(data[2:])
        if len(raw_bytes) < 64:
            print(f"⛔ Skipping: Data too short ({len(raw_bytes)} bytes)")
            return None

        # Decode the first 2 values: amount0 and amount1 (both int256)
        amount0 = int.from_bytes(raw_bytes[0:32], byteorder="big", signed=True)
        amount1 = int.from_bytes(raw_bytes[32:64], byteorder="big", signed=True)

        # Determine swap direction and flow based on signs
        if amount0 < 0 and amount1 > 0:
            direction = "token0→token1"
            amount_in = abs(amount0)
            amount_out = abs(amount1)
        elif amount1 < 0 and amount0 > 0:
            direction = "token1→token0"
            amount_in = abs(amount1)
            amount_out = abs(amount0)
        else:
            direction = "ambiguous"
            amount_in = abs(amount0)
            amount_out = abs(amount1)
            print(f"⚠️ Ambiguous swap amounts: amount0={amount0}, amount1={amount1}")

        print(f"🟢 Decoded Uniswap V3 Swap: {amount_in} in → {amount_out} out")

        return {
            "event": "uniswap_v3_swap",
            "direction": direction,
            "from": sender,
            "to": recipient,
            "amount_in": float(amount_in),
            "amount_out": float(amount_out),
            "tx_hash": log.get("transactionHash"),
            "block_number": int(log.get("blockNumber", "0x0"), 16),
            "contract": log.get("address")
        }

    except Exception as e:
        print(f"❌ Exception during Uniswap V3 decode: {e}")
        return None
