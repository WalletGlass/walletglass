# walletglass/ingestion/parser.py

"""
Parser module that orchestrates:
1. Fetching transfers and logs from Alchemy
2. Decoding logs using modular decoders
3. Building normalized Transaction objects
"""

from ingestion.alchemy_adapter import fetch_txs_and_logs
from ingestion.decoder import decode_logs
from core.build_transaction import build_transaction

def parse_wallet(address: str):
    print(f"🔍 Parsing wallet: {address}")
    
    raw_data = fetch_txs_and_logs(address)

    transactions = []

    for tx in raw_data:
        tx_hash = tx.get("tx_hash")
        logs = tx.get("logs", [])

        decoded_logs = decode_logs(logs)
        tx_obj = build_transaction(tx, decoded_logs)

        if tx_obj:
            transactions.append(tx_obj)

    print(f"📦 Decoding {len(transactions)} transactions...")
    print(f"✅ Parsed {len(transactions)} Transaction objects\n")
    return transactions
