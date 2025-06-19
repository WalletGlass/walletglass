from decimal import Decimal

# Ignore incoming transfers smaller than this (USD equivalent will come later)
MIN_FUNDING_USD = Decimal("10")

# Example known spam/token addresses to filter out
IGNORED_TOKEN_ADDRESSES = {
    "0x000000000000000000000000000000000000dead",  # burn
    "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",  # pseudo-native
}

# Default ETH token symbol/address
ETH_TOKEN_SYMBOL = "ETH"
ETH_ADDRESS = "0x0000000000000000000000000000000000000000"

# Useful decimals
GWEI_IN_ETH = Decimal("1000000000")
