"""
pricing_engine.py

ETH pricing module for WalletGlass.

- Loads static ETH/USD prices from eth_prices.json
- Attempts real-time and historical fetches from CryptoCompare (primary)
- Falls back to yfinance (secondary) if API fails
- Includes internal caching for efficiency
- Exposes `get_price_at_time()` and `fetch_current_eth_price()` for use across modules

This file is critical for accurate USD-denominated PnL calculations.
"""

import os
import json
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime
from decimal import Decimal
from rich import print

# -----------------------------
# GLOBAL CACHES
# -----------------------------
_price_cache = {}
STATIC_PRICE_CACHE = {}

# -----------------------------
# LOAD STATIC PRICES FROM JSON
# -----------------------------
try:
    json_path = os.path.join(os.path.dirname(__file__), "..", "data", "eth_prices.json")

    with open(json_path, "r") as f:
        raw_prices = json.load(f)
        STATIC_PRICE_CACHE = {
            date: Decimal(str(price)) for date, price in raw_prices.items()
        }
        print(f"[green]✔ Loaded {len(STATIC_PRICE_CACHE)} static prices from eth_prices.json[/green]")
except Exception as e:
    print(f"[red]❌ Failed to load static price cache: {e}[/red]")

# -----------------------------
# CRYPTOCOMPARE HISTORICAL DAILY API
# -----------------------------
def fetch_eth_prices_by_range(start_ts: int, end_ts: int) -> dict:
    """
    Fetch ETH/USD daily prices from CryptoCompare API for the range.
    Returns a dictionary with 'YYYY-MM-DD' as keys and Decimal prices.
    """
    print(f"> Fetching ETH prices from {start_ts} to {end_ts}...")
    url = "https://min-api.cryptocompare.com/data/v2/histoday"
    params = {
        "fsym": "ETH",
        "tsym": "USD",
        "limit": 2000,
        "toTs": end_ts,
    }
    response = requests.get(url, params=params)
    data = response.json()

    if data.get("Response") != "Success":
        print("[yellow]⚠ CryptoCompare failed, falling back to yfinance...[/yellow]")
        return fetch_eth_prices_from_yfinance(start_ts, end_ts)

    prices = {}
    for entry in data["Data"]["Data"]:
        date = datetime.utcfromtimestamp(entry["time"]).strftime("%Y-%m-%d")
        prices[date] = Decimal(str(entry["close"]))

    return prices

# -----------------------------
# FALLBACK: YFINANCE
# -----------------------------
def fetch_eth_prices_from_yfinance(start_ts: int, end_ts: int) -> dict:
    """
    Use yfinance to get ETH-USD daily close prices in the given range.
    """
    start_dt = datetime.utcfromtimestamp(start_ts).strftime("%Y-%m-%d")
    end_dt = datetime.utcfromtimestamp(end_ts).strftime("%Y-%m-%d")
    print(f">> Pulling fallback daily ETH prices via yfinance from {start_dt} to {end_dt}")

    df = yf.download("ETH-USD", start=start_dt, end=end_dt, progress=False)
    if df.empty:
        print("[red]❌ Error: No price data returned[/red]")
        return {}

    prices = {}
    for date, row in df.iterrows():
        date_str = date.strftime("%Y-%m-%d")
        prices[date_str] = Decimal(str(row["Close"]))

    return prices

# -----------------------------
# PRICE LOOKUP
# -----------------------------
def get_price_at_time(timestamp: int) -> Decimal:
    """
    Returns the daily average ETH price for a given UNIX timestamp.
    Tries cache → static → yfinance (as fallback).
    """
    tx_time = datetime.utcfromtimestamp(timestamp)
    date_str = tx_time.strftime("%Y-%m-%d")

    # Cache lookup
    if date_str in _price_cache:
        return _price_cache[date_str]

    # Static cache fallback
    if date_str in STATIC_PRICE_CACHE:
        price = STATIC_PRICE_CACHE[date_str]
        _price_cache[date_str] = price
        print(f"[green]✔ Used static cached price for {date_str}: ${price}[/green]")
        return price

    # Try yfinance fallback
    print(f"[yellow]⚠ No price found for {date_str}, attempting yfinance...[/yellow]")
    try:
        df = yf.download("ETH-USD", start=date_str, end=date_str, interval="1d", progress=False)
        if not df.empty:
            close_price = df["Close"].iloc[0]
            price_decimal = Decimal(str(close_price)).quantize(Decimal("0.01"))
            _price_cache[date_str] = price_decimal
            return price_decimal
        else:
            print(f"[red]❌ yfinance had no data for {date_str}[/red]")
    except Exception as e:
        print(f"[red]❌ yfinance error on {date_str}: {e}[/red]")

    return Decimal("0.0")

# -----------------------------
# CURRENT PRICE FETCH
# -----------------------------
def fetch_current_eth_price() -> Decimal:
    """
    Fetches the current ETH price in USD from CryptoCompare.
    Falls back to 0.0 on failure.
    """
    url = "https://min-api.cryptocompare.com/data/price"
    params = {"fsym": "ETH", "tsyms": "USD"}
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if "USD" in data:
            return Decimal(str(data["USD"]))
        else:
            print(f"[red]❌ Failed to fetch current ETH price: {data}[/red]")
            return Decimal("0.0")
    except Exception as e:
        print(f"[red]❌ Error fetching current ETH price: {e}[/red]")
        return Decimal("0.0")
