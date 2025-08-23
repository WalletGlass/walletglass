# 🪙 erc20.py — ERC20 Transfer Decoder
"""
Extracts and normalizes ERC20 `Transfer` events from transaction logs.
Returns a list of TokenTransfer objects for use in funding, balance tracking, and PnL.
"""

from walletglass_core.processing.models import TokenTransfer

# ERC20 Transfer event signature hash
TRANSFER_EVENT_SIG = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# -----------------------------
# 🧮 Decode Transfer Logs
# -----------------------------
def extract_erc20_transfers(logs):
    """
    Extracts ERC20 Transfer events from logs.
    Assumes logs are already pulled from Alchemy receipt.
    """
    transfers = []

    for log in logs:
        if log.get("topics", [])[0].lower() != TRANSFER_EVENT_SIG:
            continue  # Not a Transfer event

        if len(log["topics"]) < 3:
            continue  # Malformed event

        try:
            from_addr = f"0x{log['topics'][1][-40:]}"
            to_addr = f"0x{log['topics'][2][-40:]}"
            raw_value = int(log["data"], 16)
            token_address = log["address"]
            token_symbol = "UNKNOWN"  # TODO: resolve symbol from cache or metadata
            value = raw_value / (10 ** 18)  # NOTE: assumes 18 decimals for now

            transfers.append(TokenTransfer(
                token=token_symbol,
                amount=value,
                from_addr=from_addr,
                to_addr=to_addr
            ))
        except Exception as e:
            print(f"⚠️ Failed to decode ERC20 transfer: {e}")
            continue

    return transfers
