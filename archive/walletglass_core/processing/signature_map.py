# 🧾 signature_map.py — Function selector to protocol/type mapping
"""
Central routing map for identifying transaction type and protocol
based on the first 4 bytes of calldata (function selector).

Used by parser.py to delegate decoding to the correct module.
"""

# Each entry maps 4-byte selector to:
# - protocol name
# - tx type (swap, fund, etc.)
# - parser function reference (to be assigned at runtime)

signature_map = {
    # Uniswap V2
    "0x38ed1739": {"protocol": "Uniswap", "type": "swap", "parser": None},
    "0x18cbafe5": {"protocol": "Uniswap", "type": "swap", "parser": None},
    "0x7ff36ab5": {"protocol": "Uniswap", "type": "swap", "parser": None},

    # Uniswap V3
    "0x5ae401dc": {"protocol": "Uniswap", "type": "swap", "parser": None},
    "0x414bf389": {"protocol": "Uniswap", "type": "swap", "parser": None},
    "0xb858183f": {"protocol": "Uniswap", "type": "swap", "parser": None},

    # Future support examples:
    # "0x7c025200": {"protocol": "1inch", "type": "swap", "parser": None},
    # "0x095ea7b3": {"protocol": "ERC20", "type": "approve", "parser": None},
}

# Assign parser references at runtime (called from parser.py)
def bind_parsers():
    from walletglass_core.protocols import uniswap  # import here to avoid circular dependency

    for selector, entry in signature_map.items():
        if entry["protocol"] == "Uniswap":
            entry["parser"] = uniswap.parse_uniswap
