# scripts/test_transfer_decode.py

import json
from ingestion.decoder import decode_transfer_event

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
YOUR_WALLET = "0x0193138F52c349A66d0b7Ccbe29d70E613E6C968".lower()

with open("data/raw_logs.json", "r") as f:
    all_log_groups = json.load(f)

count = 0

for group in all_log_groups:
    if isinstance(group, list):
        for log in group:
            if isinstance(log, dict) and "topics" in log and len(log["topics"]) > 0:
                if log["topics"][0].lower() == TRANSFER_TOPIC:
                    try:
                        decoded = decode_transfer_event(log, YOUR_WALLET)
                        print(decoded)
                        count += 1
                    except Exception as e:
                        print(f"❌ Failed to decode log: {e}")

print(f"\n✅ Decoded {count} ERC-20 Transfer logs")
