// Ledger Live "operation history" CSV export.
// IN/OUT are imported as transfers (no tax effect). Payments to third parties must be
// reclassified as sells by hand; the EUR countervalue from Ledger is kept as a hint in the note.
import { parseCsv } from '../csv.js';
import { normalize } from '../ledger.js';

const TYPE_MAP = { IN: 'transfer_in', OUT: 'transfer_out' };

export function importLedgerLive(text) {
  const txs = [], errors = [];
  parseCsv(text).forEach((r, i) => {
    const type = TYPE_MAP[(r['Operation Type'] || '').toUpperCase()];
    if (!type) return; // FEES, DELEGATE, etc.: skipped
    try {
      const cv = r['Countervalue Ticker'] === 'EUR' ? r['Countervalue at Operation Date'] : '';
      txs.push(normalize({
        date: r['Operation Date'], type, asset: r['Currency Ticker'], amount: r['Operation Amount'],
        eurValue: '', feeEur: 0, source: 'ledger:' + (r['Account Name'] || ''),
        ref: r['Operation Hash'], note: cv ? `Ledger countervalue ${cv} EUR` : '',
      }));
    } catch (e) {
      errors.push(`row ${i + 2}: ${e.message}`);
    }
  });
  return { txs, errors };
}
