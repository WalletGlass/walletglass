"""
Builds eth_price_db.json from data/etherprice.csv
Format expected: "Date(UTC)","Timestamp","Value"
"""

import pandas as pd
import json
from pathlib import Path

csv_path = Path("data/etherprice.csv")
output_path = Path("data/eth_price_db.json")

# Load with correct headers
df = pd.read_csv(csv_path)

# Use exact headers
date_col = "Date(UTC)"
price_col = "Value"

# Convert: "YYYY-MM-DD" → float price
eth_price_db = {
    pd.to_datetime(row[date_col]).strftime("%Y-%m-%d"): float(row[price_col])
    for _, row in df.iterrows()
    if pd.notnull(row[price_col])
}

# Save to JSON
Path("data").mkdir(exist_ok=True)
with open(output_path, "w") as f:
    json.dump(eth_price_db, f, indent=2)

print(f"✅ Saved ETH daily price DB to {output_path}")
print(f"🪙 Loaded {len(eth_price_db)} daily price points.")
