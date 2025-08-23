import requests, os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MORALIS_API_KEY")
wallet = "0x0193138F52c349A66d0b7Ccbe29d70E613E6C968"
url = f"https://deep-index.moralis.io/api/v2.2/wallets/{wallet}/history"
params = {
    "chain": "eth",
    "type": "erc20transfer",
    "order": "asc"
}
headers = {"X-API-Key": API_KEY}

res = requests.get(url, params=params, headers=headers)
data = res.json()

print(f"Found {len(data.get('result', []))} ERC-20 transfers\n")
for i, tx in enumerate(data["result"][:3]):  # show first 3
    print(f"\n🔹 Transfer #{i + 1}")
    for k, v in tx.items():
        print(f"{k}: {v}")
