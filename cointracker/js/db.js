// Local persistence. localStorage keeps the MVP simple; swap for IndexedDB if data outgrows ~5 MB.
const KEY = 'cointracker.transactions.v1';

export function load() {
  try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch { return []; }
}

export function save(list) {
  localStorage.setItem(KEY, JSON.stringify(list));
}

export function exportJson(list) {
  return JSON.stringify({ version: 1, transactions: list }, null, 2);
}

export function parseBackup(text) {
  const data = JSON.parse(text);
  if (!Array.isArray(data.transactions)) throw new Error('Not a CoinTracker backup');
  return data.transactions;
}
