const wallets = require('crypto-exchange-wallets');
const all = wallets.ethereum.walletsByExchange;

const flat = [];

for (const [label, addresses] of Object.entries(all)) {
  if (Array.isArray(addresses)) {
    addresses.forEach((address) => {
      flat.push({
        address: address.toLowerCase(),
        label: label.toLowerCase(),
        type: "cex"
      });
    });
  } else {
    console.warn(`⚠️ Skipped ${label} — value was not an array`);
  }
}

console.log(JSON.stringify(flat, null, 2));
