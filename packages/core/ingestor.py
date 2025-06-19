from .transaction import Transaction
from datetime import datetime
from decimal import Decimal
from typing import List

def load_wallet_transactions(wallet_address: str) -> List[Transaction]:
    """
    TEMPORARY: Returns dummy transactions to simulate ingestion.
    Later, this will pull from Etherscan or another data source.
    """
    return [
        Transaction(
            tx_hash="0xabc123",
            timestamp=datetime(2024, 1, 1, 12, 0),
            from_address="0xExternal1",
            to_address=wallet_address,
            value_eth=Decimal("1.25"),
            gas_used=21000,
            gas_price_gwei=Decimal("30"),
            tx_type="funding"
        ),
        Transaction(
            tx_hash="0xdef456",
            timestamp=datetime(2024, 1, 5, 8, 30),
            from_address=wallet_address,
            to_address="0xExternal2",
            value_eth=Decimal("0.5"),
            gas_used=25000,
            gas_price_gwei=Decimal("42"),
            tx_type="send"
        )
    ]
