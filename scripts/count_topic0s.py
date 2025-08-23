# scripts/count_topic0s.py

import json
from collections import defaultdict

input_path = "data/raw_logs.json"
output_path = "data/topic0_counts.json"

# Count appearances of each topic0
topic_counts = defaultdict(int)

with open(input_path, "r") as f:
    all_log_groups = json.load(f)

for group in all_log_groups:
    if isinstance(group, list):
        for log in group:
            if isinstance(log, dict) and "topics" in log and len(log["topics"]) > 0:
                topic0 = log["topics"][0].lower()
                topic_counts[topic0] += 1

# Sort by count, descending
sorted_topics = dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True))

# Write to JSON
with open(output_path, "w") as f:
    json.dump(sorted_topics, f, indent=2)

print(f"✅ Wrote topic0 counts to {output_path}")
