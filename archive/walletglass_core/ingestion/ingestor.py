# ingestor.py
"""
WalletGlass Ingestor – Alchemy-Powered Transaction Collector

This module orchestrates wallet transaction ingestion using the Alchemy API.
It fetches:
- Normal transactions
- Internal transfers
- Event logs
- (Optionally) Decoded function inputs

Resulting tx data is passed downstream for:
- Swap detection
- PnL analysis
- Protocol classification
- AI summary generation

Future: Chain-agnostic ingestion wrapper
"""

import os
from dotenv import load_dotenv
from walletglass_core.ingestion.alchemy import (
    get_normal_transactions,
    get_internal_transactions,
    get_logs_for_tx,
    get_decoded_tx_input
)
from walletglass_core.processing.transaction_normalizer import normalize_all

load_dotenv()

def ingest_wallet_activity(address):
    """Pulls all relevant tx data for a wallet via Alchemy."""
    print(f"\n🚀 Ingesting wallet activity for {address}...")

    normal_txs = get_normal_transactions(address)
    print(f"✅ Normal txs fetched: {len(normal_txs)}")

    internal_txs = get_internal_transactions(address)
    print(f"✅ Internal txs fetched: {len(internal_txs)}")

    enriched_txs = []

    for tx in normal_txs:
        tx_hash = tx.get("hash")
        if not tx_hash:
            continue

        logs = get_logs_for_tx(tx_hash)
        decoded_input = get_decoded_tx_input(tx_hash)

        enriched_txs.append({
            "tx": tx,
            "logs": logs,
            "decoded_input": decoded_input,
        })

    normalized = normalize_all(enriched_txs)

    return {
        "normal": normal_txs,
        "internal": internal_txs,
        "enriched": enriched_txs,
        "normalized": normalized
    }

# For testing/debugging
if __name__ == "__main__":
    test_wallet = "0x4Ac92D60CB6415232E62db519657c33ABdcd102F"
    data = ingest_wallet_activity(test_wallet)
    print(f"\n🧠 Parsed {len(data['enriched'])} enriched txs.")