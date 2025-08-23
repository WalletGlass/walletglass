"""
Test: Decoder Pipeline
----------------------
Uses sample logs from AlchemyAdapter to test decoding.
"""

from ingestion.alchemy_adapter import fetch_txs_and_logs
from ingestion.decoder import decode_logs

if __name__ == "__main__":
    test_wallet = "0x0193138F52c349A66d0b7Ccbe29d70E613E6C968"
    raw = fetch_txs_and_logs(test_wallet)

    logs = raw.get("logs", [])
    print(f"📦 Found {len(logs)} logs")

    decoded = decode_logs(logs)
    print(f"✅ Decoded {len(decoded)} events")

    for event in decoded[:3]:
        print(event)
