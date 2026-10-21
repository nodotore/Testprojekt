// Generic CSV: date,type,asset,amount,eur_value,fee_eur,source,note,ref
import { parseCsv } from '../csv.js';
import { normalize } from '../ledger.js';

export const GENERIC_HEADER = 'date,type,asset,amount,eur_value,fee_eur,source,note,ref';

export function importGeneric(text) {
  const txs = [], errors = [];
  parseCsv(text).forEach((r, i) => {
    try {
      txs.push(normalize({
        date: r.date, type: r.type, asset: r.asset, amount: r.amount.replace(',', '.'),
        eurValue: r.eur_value.replace(',', '.'), feeEur: (r.fee_eur || '0').replace(',', '.'),
        source: r.source || 'csv', note: r.note, ref: r.ref,
      }));
    } catch (e) {
      errors.push(`row ${i + 2}: ${e.message}`);
    }
  });
  return { txs, errors };
}
