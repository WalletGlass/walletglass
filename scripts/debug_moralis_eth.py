import requests, os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("MORALIS_API_KEY")
wallet = "0x0193138F52c349A66d0b7Ccbe29d70E613E6C968"

url = f"https://deep-index.moralis.io/api/v2.2/wallets/{wallet}/history"
params = {
    "chain": "eth",
    "type": "transaction",  # native ETH transfers
    "order": "asc"
}
headers = {"X-API-Key": API_KEY}

res = requests.get(url, params=params, headers=headers)
data = res.json()

print(f"Found {len(data.get('result', []))} ETH transactions\n")

# Print structure of first 2 txs
for i, tx in enumerate(data["result"][:10]):
    print(f"\n🔹 ETH Tx #{i+1}")
    print(f"tx_hash: {tx['hash']}")
    print(f"block: {tx['block_number']}")
    print("native_transfers:")
    for t in tx.get("native_transfers", []):
        for k, v in t.items():
            print(f"  {k}: {v}")
