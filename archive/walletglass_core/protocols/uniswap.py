# 🔄 uniswap.py — Parser for Uniswap V2, V3, and basic V4 support
"""
Decodes Uniswap transactions using input data and logs.
Supports V2 and V3 by identifying function signatures.
Provides minimal V4 support by detecting V4 router and flagging swap_v4 type.
Returns a ParsedTx object for consistency across the WalletGlass pipeline.
"""

from walletglass_core.processing.models import ParsedTx, TokenTransfer

# Known 4-byte function selectors for Uniswap V2 & V3 swaps
UNISWAP_SELECTORS = {
    "0x38ed1739": "swapExactTokensForTokens",    # V2
    "0x18cbafe5": "swapExactETHForTokens",       # V2
    "0x7ff36ab5": "swapExactETHForTokensSupportingFeeOnTransferTokens",
    "0x5ae401dc": "multicall",                   # V3 router
    "0x414bf389": "exactInputSingle",           # V3 swap
    "0xb858183f": "exactInput",                 # V3 multi-hop
}

UNISWAP_V4_ROUTER = "0xef1c6e67703c7bd7107eed8303fbe6ec2554bf6b"  # Canonical V4 singleton router

# Placeholder symbol resolution (mock)
def resolve_token_symbol(address):
    return "UNKNOWN"

# Placeholder amount resolution (mock)
def decode_swap_amounts(tx_logs):
    # TODO: Decode `Swap` event logs to extract amounts and token addresses
    return ["ETH", "USDC"], [1.0, 3725.0]  # example output

def parse_uniswap(tx_raw):
    """
    Attempts to parse a Uniswap swap transaction.
    Handles V2, V3 (via selector), and basic V4 (via router address).
    Assumes tx_raw contains:
        - 'hash'
        - 'to'
        - 'from'
        - 'rawContract': { 'address': ... }
        - 'rawInput': hex calldata string
    """
    tx_hash = tx_raw.get("hash")
    to_addr = tx_raw.get("to", "").lower()
    method_id = tx_raw.get("rawInput", "0x")[:10]

    # V4 basic detection via singleton router
    if to_addr == UNISWAP_V4_ROUTER:
        return ParsedTx(
            hash=tx_hash,
            protocol="Uniswap",
            type="swap_v4",
            tokens=[],
            amounts=[],
            transfers=[],
            internals=[],
            raw=tx_raw
        )

    # Handle V2/V3 via selector
    if method_id not in UNISWAP_SELECTORS:
        raise ValueError("Unknown Uniswap method selector")

    token_symbols, amounts = decode_swap_amounts([])  # logs passed in later

    return ParsedTx(
        hash=tx_hash,
        protocol="Uniswap",
        type="swap",
        tokens=token_symbols,
        amounts=amounts,
        transfers=[],
        internals=[],
        raw=tx_raw
    )
