import test from 'node:test';
import assert from 'node:assert/strict';
import { normalize, mergeUnique } from '../js/ledger.js';
import { computeFifo, yearSummary } from '../js/tax.js';
import { parseCsv } from '../js/csv.js';
import { importGeneric } from '../js/import/generic.js';
import { importLedgerLive } from '../js/import/ledgerlive.js';

const tx = (date, type, amount, eurValue, extra = {}) =>
  normalize({ date, type, asset: 'BTC', amount, eurValue, ...extra });

test('FIFO consumes oldest lot first and computes the gain', () => {
  const r = computeFifo([
    tx('2024-01-01', 'buy', 1, 20000),
    tx('2024-02-01', 'buy', 1, 30000),
    tx('2024-06-01', 'sell', 1.5, 60000),
  ]);
  assert.equal(r.disposals.length, 2);
  assert.equal(r.disposals[0].cost, 20000);
  assert.equal(r.disposals[0].proceeds, 40000);
  assert.equal(r.disposals[1].cost, 15000);
  assert.equal(r.disposals[1].gain, 20000 - 15000);
  assert.deepEqual(r.holdings.BTC, { amount: 0.5, cost: 15000 });
});

test('sale more than one year after purchase is tax-free', () => {
  const r = computeFifo([
    tx('2023-03-01', 'buy', 1, 20000),
    tx('2024-03-01', 'sell', 1, 40000), // exactly one year: still taxable
    tx('2023-03-01T00:00:00Z', 'buy', 1, 20000, { ref: 'b' }),
    tx('2024-03-02', 'sell', 1, 40000),
  ]);
  assert.equal(r.disposals[0].taxFree, false);
  assert.equal(r.disposals[1].taxFree, true);
});

test('fees raise cost on buys and reduce proceeds on sells', () => {
  const r = computeFifo([
    tx('2024-01-01', 'buy', 1, 1000, { feeEur: 10 }),
    tx('2024-02-01', 'sell', 1, 2000, { feeEur: 20 }),
  ]);
  assert.equal(r.disposals[0].cost, 1010);
  assert.equal(r.disposals[0].gain, 1980 - 1010);
});

test('transfers do not create disposals or lots', () => {
  const r = computeFifo([
    tx('2024-01-01', 'buy', 1, 1000),
    tx('2024-01-05', 'transfer_out', 1, ''),
    tx('2024-01-05', 'transfer_in', 1, '', { ref: 'x' }),
  ]);
  assert.equal(r.disposals.length, 0);
  assert.equal(r.holdings.BTC.amount, 1);
});

test('selling more than owned warns and assumes zero cost', () => {
  const r = computeFifo([tx('2024-01-01', 'sell', 1, 500)]);
  assert.equal(r.warnings.length, 1);
  assert.equal(r.disposals[0].missingCost, true);
  assert.equal(r.disposals[0].gain, 500);
});

test('Freigrenze: 1000 EUR from 2024, whole gain taxable once reached', () => {
  const below = yearSummary(computeFifo([tx('2024-01-01', 'buy', 1, 1000), tx('2024-02-01', 'sell', 1, 1999)]), 2024);
  assert.equal(below.privateSalesTaxable, 0);
  const at = yearSummary(computeFifo([tx('2024-01-01', 'buy', 1, 1000), tx('2024-02-01', 'sell', 1, 2000)]), 2024);
  assert.equal(at.privateSalesTaxable, 1000);
  const old = yearSummary(computeFifo([tx('2023-01-01', 'buy', 1, 1000), tx('2023-02-01', 'sell', 1, 1700)]), 2023);
  assert.equal(old.freigrenze, 600);
  assert.equal(old.privateSalesTaxable, 700);
});

test('income is reported and enters FIFO at market value', () => {
  const r = computeFifo([
    tx('2024-01-01', 'income', 0.1, 300),
    tx('2024-02-01', 'sell', 0.1, 400),
  ]);
  const s = yearSummary(r, 2024);
  assert.equal(s.income, 300);
  assert.equal(s.incomeTaxable, 300);
  assert.equal(r.disposals[0].gain, 100);
});

test('CSV parser handles quotes and semicolons', () => {
  assert.deepEqual(parseCsv('a;b\n"x;1";"he said ""hi"""\n'), [{ a: 'x;1', b: 'he said "hi"' }]);
});

test('generic import reports bad rows and accepts decimal comma', () => {
  const { txs, errors } = importGeneric(
    'date,type,asset,amount,eur_value,fee_eur,source,note,ref\n' +
    '2024-01-01,buy,btc,"0,5","1000,50",0,test,,\n' +
    '2024-01-02,swap,btc,1,1,0,test,,\n');
  assert.equal(txs.length, 1);
  assert.equal(txs[0].amount, 0.5);
  assert.equal(txs[0].eurValue, 1000.5);
  assert.equal(errors.length, 1);
});

test('Ledger Live import maps IN/OUT to transfers and skips fees', () => {
  const csv = 'Operation Date,Currency Ticker,Operation Type,Operation Amount,Operation Fees,Operation Hash,Account Name,Account xpub,Countervalue Ticker,Countervalue at Operation Date,Countervalue at CSV Export\n' +
    '2024-01-01T10:00:00.000Z,BTC,IN,0.5,0,h1,Bitcoin 1,xpub,EUR,20000,25000\n' +
    '2024-01-02T10:00:00.000Z,BTC,FEES,0.0001,0,h2,Bitcoin 1,xpub,EUR,4,5\n';
  const { txs } = importLedgerLive(csv);
  assert.equal(txs.length, 1);
  assert.equal(txs[0].type, 'transfer_in');
  assert.match(txs[0].note, /20000/);
});

test('mergeUnique skips duplicates on re-import', () => {
  const a = tx('2024-01-01', 'buy', 1, 1000, { source: 's', ref: 'r' });
  const { added, skipped } = mergeUnique([a], [{ ...a, id: 'other' }]);
  assert.equal(added.length, 0);
  assert.equal(skipped.length, 1);
});
