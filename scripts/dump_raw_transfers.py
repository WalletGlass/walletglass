# scripts/dump_raw_transfers.py

import json
from ingestion.alchemy_adapter import fetch_transfers

address = "0x0193138F52c349A66d0b7Ccbe29d70E613E6C968"
print(f"🔍 Fetching raw transfers for: {address}")

transfers = fetch_transfers(address)

with open("data/raw_transfers.json", "w") as f:
    json.dump(transfers, f, indent=2)

print(f"✅ Dumped {len(transfers)} raw transfer objects to data/raw_transfers.json")
