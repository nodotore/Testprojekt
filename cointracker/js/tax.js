// German private sales (§23 EStG) with FIFO. Simplified MVP, no tax advice:
// - one global FIFO queue per asset (not per wallet)
// - a disposal is tax-free when sold more than one year after acquisition
// - fees on buys add to cost, fees on sells reduce proceeds
// - income (staking, airdrops) is taxed on receipt (§22 Nr. 3), then enters FIFO at market value
import { sortTx } from './ledger.js';

const EPS = 1e-12;

export function oneYearLater(iso) {
  const d = new Date(iso);
  d.setUTCFullYear(d.getUTCFullYear() + 1);
  return d;
}

export function computeFifo(transactions) {
  const lots = new Map();
  const disposals = [];
  const income = [];
  const warnings = [];

  for (const tx of sortTx(transactions)) {
    const queue = lots.get(tx.asset) ?? lots.set(tx.asset, []).get(tx.asset);
    if (tx.type === 'buy' || tx.type === 'income') {
      queue.push({ date: tx.date, amount: tx.amount, cost: tx.eurValue + (tx.type === 'buy' ? tx.feeEur : 0) });
      if (tx.type === 'income') income.push({ date: tx.date, asset: tx.asset, amount: tx.amount, eurValue: tx.eurValue });
    } else if (tx.type === 'sell') {
      const proceedsTotal = tx.eurValue - tx.feeEur;
      let remaining = tx.amount;
      while (remaining > EPS) {
        let lot = queue[0];
        let missingCost = false;
        if (!lot) {
          warnings.push(`${tx.date.slice(0, 10)} ${tx.asset}: sold ${remaining} more than acquired, cost basis 0 assumed`);
          lot = { date: tx.date, amount: remaining, cost: 0 };
          missingCost = true;
        }
        const used = Math.min(remaining, lot.amount);
        const cost = lot.cost * (used / lot.amount);
        const proceeds = proceedsTotal * (used / tx.amount);
        const taxFree = new Date(tx.date) > oneYearLater(lot.date);
        disposals.push({
          asset: tx.asset, soldAt: tx.date, acquiredAt: lot.date, amount: used,
          proceeds, cost, gain: proceeds - cost, taxFree, missingCost,
        });
        if (!missingCost) {
          lot.cost -= cost;
          lot.amount -= used;
          if (lot.amount <= EPS) queue.shift();
        }
        remaining -= used;
      }
    }
  }
  return { disposals, income, warnings, holdings: holdings(lots) };
}

function holdings(lots) {
  const out = {};
  for (const [asset, queue] of lots) {
    const amount = queue.reduce((s, l) => s + l.amount, 0);
    if (amount > EPS) out[asset] = { amount, cost: queue.reduce((s, l) => s + l.cost, 0) };
  }
  return out;
}

// Freigrenze (not an allowance): once exceeded, the full amount is taxable.
export const freigrenzePrivateSales = year => (year >= 2024 ? 1000 : 600);
export const FREIGRENZE_INCOME = 256;

export function yearSummary(result, year) {
  const inYear = d => new Date(d).getUTCFullYear() === year;
  const sales = result.disposals.filter(d => inYear(d.soldAt));
  const taxable = sales.filter(d => !d.taxFree);
  const gains = taxable.reduce((s, d) => s + d.gain, 0);
  const incomeTotal = result.income.filter(i => inYear(i.date)).reduce((s, i) => s + i.eurValue, 0);
  const limit = freigrenzePrivateSales(year);
  return {
    year,
    taxableGain: gains,
    taxFreeGain: sales.filter(d => d.taxFree).reduce((s, d) => s + d.gain, 0),
    freigrenze: limit,
    privateSalesTaxable: gains >= limit ? gains : 0,
    income: incomeTotal,
    incomeFreigrenze: FREIGRENZE_INCOME,
    incomeTaxable: incomeTotal >= FREIGRENZE_INCOME ? incomeTotal : 0,
    disposals: sales,
  };
}
