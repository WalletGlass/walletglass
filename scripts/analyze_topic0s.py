"""
Analyze Topic0s
---------------
Scans logs across parsed transactions to find unknown topic0s.
Helps prioritize which decoders to implement next.
"""

import json
from collections import defaultdict
from ingestion.alchemy_adapter import fetch_txs_and_logs, fetch_tx_receipt
from ingestion.decoder import TOPIC0_DECODERS

def analyze_topic0s(wallet: str):
    print(f"🔍 Analyzing unknown topic0s for: {wallet}")

    raw = fetch_txs_and_logs(wallet)
    txs = raw.get("transactions", [])
    topic_counts = defaultdict(int)

    for tx in txs:
        tx_hash = tx.get("hash")
        if not tx_hash:
            continue

        receipt = fetch_tx_receipt(tx_hash)
        logs = receipt.get("logs", [])
        for log in logs:
            topics = log.get("topics", [])
            if not topics:
                continue

            topic0 = topics[0].lower()
            if topic0 not in TOPIC0_DECODERS:
                topic_counts[topic0] += 1

    sorted_topic_counts = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)

    print(f"\n✅ Found {len(sorted_topic_counts)} unknown topic0s")
    output = {k: v for k, v in sorted_topic_counts}
    with open("data/topic0_unknown_counts.json", "w") as f:
        json.dump(output, f, indent=2)

    print("📁 Output written to: data/topic0_unknown_counts.json")

if __name__ == "__main__":
    wallet = "0x0193138F52c349A66d0b7Ccbe29d70E613E6C968"
    analyze_topic0s(wallet)
