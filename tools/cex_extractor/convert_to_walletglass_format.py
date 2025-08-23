import json

with open("known_funding_sources_flat.json") as f:
    flat = json.load(f)

# Convert to WalletGlass key-value format
formatted = {
    entry["address"]: {
        "label": entry["label"],
        "type": entry["type"]
    }
    for entry in flat
}

with open("../../data/known_funding_sources.json", "w") as out:
    json.dump(formatted, out, indent=2)

print(f"✅ Saved {len(formatted)} entries to known_funding_sources.json")
