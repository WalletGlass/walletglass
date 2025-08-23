# 🔮 alchemy.py — Alchemy-based transaction fetcher for WalletGlass

import os
import requests
from dotenv import load_dotenv

load_dotenv()

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
BASE_URL = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

HEADERS = {
    "Content-Type": "application/json",
}

# ----------------------------
# 🔧 JSON-RPC Request Helper
# ----------------------------
def make_rpc_request(method, params):
    response = requests.post(
        BASE_URL,
        headers=HEADERS,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        },
    )
    response.raise_for_status()
    return response.json().get("result")

# ----------------------------------------
# 📥 Fetch Normal Transactions
# ----------------------------------------
def get_normal_transactions(address, start_block="0x0", end_block="latest"):
    return make_rpc_request("alchemy_getAssetTransfers", [
        {
            "fromBlock": start_block,
            "toBlock": end_block,
            "fromAddress": address,
            "toAddress": address,
            "category": ["external", "erc20", "erc721", "erc1155"],
            "withMetadata": True,
            "excludeZeroValue": True,
        }
    ])

# ----------------------------------------
# 🔍 Fetch Internal Transactions
# ----------------------------------------
def get_internal_transactions(tx_hash):
    return make_rpc_request("alchemy_getTransactionReceipts", [
        {"transactionHashes": [tx_hash]}
    ])

# ----------------------------------------
# 📊 Fetch Logs for a Transaction
# ----------------------------------------
def get_transaction_receipt(tx_hash):
    return make_rpc_request("eth_getTransactionReceipt", [tx_hash])

# ----------------------------------------
# 🧠 Decode Function Input (if ABI known)
# ----------------------------------------
def get_transaction(tx_hash):
    return make_rpc_request("eth_getTransactionByHash", [tx_hash])

# Example Usage (for dev/testing only)
if __name__ == "__main__":
    wallet = "0x4Ac92D60CB6415232E62db519657c33ABdcd102F"
    transfers = get_normal_transactions(wallet)
    print(f"Fetched {len(transfers)} normal transfers")
