"""
Log Decoder Router
------------------
Inspects log topic0 and dispatches to the appropriate decoder module.
Logs unknown events.
"""

from typing import List, Dict, Any
from ingestion.decoder_modules.transfer import decode_transfer
from ingestion.decoder_modules.uniswap_v3 import decode_uniswap_v3

# Map of known topic0 → decoder function
TOPIC0_DECODERS = {
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": decode_transfer,  # ERC20/721 Transfer
    "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822": decode_uniswap_v3

}

def decode_logs(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Decodes a list of logs. Returns a list of decoded event dicts.
    Unknown logs are skipped with a warning.
    """
    decoded_events = []

    for log in logs:
        topic0 = log.get("topics", [None])[0]
        if not topic0:
            continue

        decoder = TOPIC0_DECODERS.get(topic0.lower())
        if decoder:
            print(f"➡️ Decoding with: {decoder.__name__} | topic0: {topic0}")

            decoded = decoder(log)
            if decoded:
                decoded_events.append(decoded)
        else:
            print(f"⚠️ Unknown topic0: {topic0}")

    return decoded_events
