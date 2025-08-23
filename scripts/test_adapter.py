"""
Test: Alchemy Adapter
---------------------
Run this script to test basic connectivity and output from fetch_txs_and_logs.
"""

import os
from ingestion.alchemy_adapter import fetch_txs_and_logs

if __name__ == "__main__":
    test_wallet = "0x0193138F52c349A66d0b7Ccbe29d70E613E6C968"  # Tyler’s test wallet

    print(f"🔍 Testing fetch for: {test_wallet}")
    data = fetch_txs_and_logs(test_wallet)

    print(f"\n✅ Fetched {len(data['transactions'])} transfers")
    for tx in data['transactions'][:3]:  # Preview first 3
        print(f"- {tx.get('hash', 'no-hash')} | {tx.get('category')} | {tx.get('value', 'N/A')}")

    print(f"\nℹ️ Logs returned: {len(data['logs'])} (currently stubbed)")
