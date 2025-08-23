import requests

BASE_URL_BAD = "https://deep-index.moralis.io/api/v2"
BASE_URL_GOOD = "https://deep-index.moralis.io/api/v2.2"
wallet = "0x0193138F52c349A66d0b7Ccbe29d70E613E6C968"
path = f"/wallets/{wallet}/history"
params = {"chain": "eth"}

print("\nTesting v2 (old):")
r1 = requests.get(BASE_URL_BAD + path, params=params)
print(r1.status_code, r1.text[:100])

print("\nTesting v2.2 (new):")
r2 = requests.get(BASE_URL_GOOD + path, params=params)
print(r2.status_code, r2.text[:100])
