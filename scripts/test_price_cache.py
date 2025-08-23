# scripts/test_price_cache.py

from mvp.price_cache import get_usd_price

eth_price = get_usd_price("ETH", 1620000000)
usdc_price = get_usd_price("0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", 1620000000)

print("ETH price:", eth_price)
print("USDC price:", usdc_price)
