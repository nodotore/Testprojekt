// Transaction model.
// buy / income  : asset amount enters, eurValue = purchase price or market value at receipt
// sell          : asset amount leaves, eurValue = proceeds (gross)
// transfer_in/out: movement between own wallets, no tax effect
// A crypto-to-crypto trade is entered as a sell plus a buy with the EUR value of each side.
export const TYPES = ['buy', 'sell', 'income', 'transfer_in', 'transfer_out'];

export function normalize(raw) {
  const tx = {
    id: raw.id || makeId(),
    date: new Date(raw.date).toISOString(),
    type: raw.type,
    asset: String(raw.asset || '').trim().toUpperCase(),
    amount: Number(raw.amount),
    eurValue: raw.eurValue === '' || raw.eurValue == null ? null : Number(raw.eurValue),
    feeEur: Number(raw.feeEur || 0),
    source: raw.source || '',
    ref: raw.ref || '',
    note: raw.note || '',
  };
  const errors = validate(tx);
  if (errors.length) throw new Error(errors.join('; '));
  return tx;
}

export function validate(tx) {
  const errors = [];
  if (Number.isNaN(Date.parse(tx.date))) errors.push('invalid date');
  if (!TYPES.includes(tx.type)) errors.push(`unknown type "${tx.type}"`);
  if (!tx.asset) errors.push('asset missing');
  if (!(tx.amount > 0)) errors.push('amount must be > 0');
  if (['buy', 'sell', 'income'].includes(tx.type) && !(tx.eurValue >= 0)) errors.push('eurValue required');
  if (!(tx.feeEur >= 0)) errors.push('invalid fee');
  return errors;
}

export function dedupKey(tx) {
  return [tx.source, tx.date, tx.type, tx.asset, tx.amount, tx.ref].join('|');
}

export function mergeUnique(existing, incoming) {
  const seen = new Set(existing.map(dedupKey));
  const added = [], skipped = [];
  for (const tx of incoming) {
    const k = dedupKey(tx);
    if (seen.has(k)) skipped.push(tx);
    else { seen.add(k); added.push(tx); }
  }
  return { merged: [...existing, ...added], added, skipped };
}

export function sortTx(list) {
  return [...list].sort((a, b) => a.date.localeCompare(b.date));
}

function makeId() {
  return globalThis.crypto?.randomUUID?.() ?? 'tx-' + Math.random().toString(36).slice(2) + Date.now().toString(36);
}
