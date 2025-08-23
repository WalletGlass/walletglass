# 🧠 parser.py — Main transaction parsing engine for WalletGlass
"""
This module coordinates fetching transaction data from Alchemy and routing
it through appropriate protocol parsers. It standardizes the output format
and prepares parsed data for further analytics (PnL, gas, AI summaries).

Key Functions:
- parse_wallet(address): Full pipeline for parsing a single wallet
- parse_transaction(tx): Detect protocol and decode one transaction

Depends on:
- alchemy.py for raw data fetching
- protocol parsers for decoding (e.g. Uniswap)
- common models (e.g. ParsedTx)
"""

from alchemy import (
    get_normal_transactions,
    get_transaction_receipt,
    get_internal_transactions,
    get_transaction,
)

# TEMP STUBS (replace with real imports later)
from protocols.uniswap import parse_uniswap  # future path

# -----------------------------
# 🔁 Protocol Routing Logic
# -----------------------------
PROTOCOL_DECODERS = {
    "Uniswap": parse_uniswap,  # Can expand with signature mapping
    # "1inch": parse_1inch,
    # "MetaMask": parse_metamask,
}

# -----------------------------
# 🧠 Transaction Parser
# -----------------------------
def parse_transaction(tx_raw):
    """Decode a single transaction by routing to the correct parser."""
    # Placeholder: naive routing based on tx.to address or method
    decoded_tx = get_transaction(tx_raw["hash"])
    input_data = decoded_tx.get("input", "0x")

    # Example: Uniswap check (to be replaced with real signature map)
    if "0x" in input_data and "swap" in tx_raw.get("rawContract", {}).get("address", "").lower():
        return parse_uniswap(tx_raw)

    return {
        "protocol": "Unknown",
        "type": "unknown",
        "details": tx_raw
    }

# -----------------------------
# 🧪 Wallet-Wide Parser
# -----------------------------
def parse_wallet(address):
    """Fetch and parse all transactions for a wallet."""
    raw_txs = get_normal_transactions(address)
    parsed = []

    for tx in raw_txs:
        try:
            parsed_tx = parse_transaction(tx)
            parsed.append(parsed_tx)
        except Exception as e:
            print(f"❌ Error parsing tx {tx['hash'][:10]}...: {e}")

    return parsed

# Example for testing
if __name__ == "__main__":
    WALLET = "0x4Ac92D60CB6415232E62db519657c33ABdcd102F"
    results = parse_wallet(WALLET)
    print(f"\nParsed {len(results)} transactions")
