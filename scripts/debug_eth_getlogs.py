import os
import requests
from dotenv import load_dotenv

load_dotenv()

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
BASE_URL = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

def test_eth_getlogs():
    print(f"🔑 Using key: {ALCHEMY_API_KEY[:6]}...")

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_getLogs",
        "params": [{
            "fromBlock": "0xc8b9d3",  # Block ~13,100,000
            "toBlock": "0xc8b9d5",    # Just 2 blocks later
            "address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # USDC contract
        }]
    }

    try:
        response = requests.post(BASE_URL, json=payload)
        response.raise_for_status()
        logs = response.json().get("result", [])
        print(f"✅ Got {len(logs)} logs.")
        if logs:
            print(logs[0])
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        print("🔍 Full response:")
        print(response.text)

if __name__ == "__main__":
    test_eth_getlogs()
