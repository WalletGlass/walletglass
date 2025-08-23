from ingestion.parser import parse_wallet
import json
from dataclasses import asdict

if __name__ == "__main__":
    wallet = "0x0193138F52c349A66d0b7Ccbe29d70E613E6C968"
    transactions = parse_wallet(wallet)

    print(f"\n🔄 Writing {len(transactions)} txs to parsed_wallet.json")
    with open("data/parsed_wallet.json", "w") as f:
        json.dump([asdict(tx) for tx in transactions], f, indent=2)
