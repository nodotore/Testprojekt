import { normalize, mergeUnique, sortTx, TYPES } from './ledger.js';
import { computeFifo, yearSummary } from './tax.js';
import { importGeneric, GENERIC_HEADER } from './import/generic.js';
import { importLedgerLive } from './import/ledgerlive.js';
import { toCsv } from './csv.js';
import { load, save, exportJson, parseBackup } from './db.js';

let txs = load();
const $ = id => document.getElementById(id);
const eur = n => new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(n);
const num = n => new Intl.NumberFormat('de-DE', { maximumFractionDigits: 8 }).format(n);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const say = (msg, bad) => { const el = $('status'); el.textContent = msg; el.className = bad ? 'bad' : 'ok'; };

function persist() { save(txs); render(); }

function render() {
  const list = sortTx(txs);
  $('tx-body').innerHTML = list.map(t => `<tr>
    <td>${esc(t.date.slice(0, 10))}</td><td>${esc(t.type)}</td><td>${esc(t.asset)}</td>
    <td class="r">${num(t.amount)}</td><td class="r">${t.eurValue == null ? '–' : eur(t.eurValue)}</td>
    <td>${esc(t.source)}</td><td>${esc(t.note)}</td>
    <td><button data-del="${esc(t.id)}" aria-label="Löschen">✕</button></td></tr>`).join('')
    || '<tr><td colspan="8">Noch keine Transaktionen.</td></tr>';

  const result = computeFifo(txs);
  const years = [...new Set(list.map(t => Number(t.date.slice(0, 4))))].sort();
  const sel = $('year');
  const current = Number(sel.value) || years.at(-1);
  sel.innerHTML = years.map(y => `<option ${y === current ? 'selected' : ''}>${y}</option>`).join('');

  $('holdings').innerHTML = Object.entries(result.holdings).map(([a, h]) =>
    `<tr><td>${esc(a)}</td><td class="r">${num(h.amount)}</td><td class="r">${eur(h.cost)}</td></tr>`).join('')
    || '<tr><td colspan="3">Keine Bestände.</td></tr>';

  const warn = result.warnings;
  $('warnings').innerHTML = warn.map(w => `<li>${esc(w)}</li>`).join('');

  if (!years.length) { $('report').innerHTML = ''; return; }
  const s = yearSummary(result, current);
  $('report').innerHTML = `
    <dl>
      <dt>Steuerpflichtiger Gewinn/Verlust (§23)</dt><dd>${eur(s.taxableGain)}</dd>
      <dt>Freigrenze ${eur(s.freigrenze)} → zu versteuern</dt><dd>${eur(s.privateSalesTaxable)}</dd>
      <dt>Steuerfrei (Haltefrist &gt; 1 Jahr)</dt><dd>${eur(s.taxFreeGain)}</dd>
      <dt>Einkünfte Staking/Airdrop (§22 Nr. 3)</dt><dd>${eur(s.income)}</dd>
      <dt>Freigrenze ${eur(s.incomeFreigrenze)} → zu versteuern</dt><dd>${eur(s.incomeTaxable)}</dd>
    </dl>
    <table><thead><tr><th>Verkauf</th><th>Anschaffung</th><th>Asset</th><th>Menge</th><th>Erlös</th><th>Kosten</th><th>Gewinn</th><th>Frist</th></tr></thead><tbody>
    ${s.disposals.map(d => `<tr><td>${d.soldAt.slice(0, 10)}</td><td>${d.acquiredAt.slice(0, 10)}</td><td>${esc(d.asset)}</td>
      <td class="r">${num(d.amount)}</td><td class="r">${eur(d.proceeds)}</td><td class="r">${eur(d.cost)}</td>
      <td class="r">${eur(d.gain)}</td><td>${d.taxFree ? 'steuerfrei' : 'steuerpflichtig'}${d.missingCost ? ' ⚠' : ''}</td></tr>`).join('')}
    </tbody></table>`;
}

function addImported({ txs: incoming, errors }, label) {
  const { merged, added, skipped } = mergeUnique(txs, incoming);
  txs = merged;
  persist();
  say(`${label}: ${added.length} neu, ${skipped.length} Duplikate, ${errors.length} Fehler${errors.length ? ' – ' + errors.slice(0, 3).join(' | ') : ''}`, errors.length > 0);
}

function download(name, content, type) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([content], { type }));
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
}

$('type').innerHTML = TYPES.map(t => `<option>${t}</option>`).join('');

$('add-form').addEventListener('submit', e => {
  e.preventDefault();
  const f = new FormData(e.target);
  try {
    const tx = normalize({
      date: f.get('date'), type: f.get('type'), asset: f.get('asset'), amount: f.get('amount'),
      eurValue: f.get('eurValue'), feeEur: f.get('feeEur') || 0, source: 'manuell', note: f.get('note'),
    });
    txs.push(tx);
    persist();
    e.target.reset();
    say('Transaktion gespeichert.');
  } catch (err) { say(err.message, true); }
});

$('tx-body').addEventListener('click', e => {
  const id = e.target.dataset?.del;
  if (id) { txs = txs.filter(t => t.id !== id); persist(); }
});

$('year').addEventListener('change', render);

for (const [id, fn, label] of [['imp-generic', importGeneric, 'CSV'], ['imp-ledger', importLedgerLive, 'Ledger Live']]) {
  $(id).addEventListener('change', async e => {
    const file = e.target.files[0];
    if (file) addImported(fn(await file.text()), label);
    e.target.value = '';
  });
}

$('imp-backup').addEventListener('change', async e => {
  const file = e.target.files[0];
  try {
    if (file) {
      const { merged, added } = mergeUnique(txs, parseBackup(await file.text()).map(normalize));
      txs = merged; persist(); say(`Backup: ${added.length} Transaktionen wiederhergestellt.`);
    }
  } catch (err) { say(err.message, true); }
  e.target.value = '';
});

$('dl-template').addEventListener('click', () => download('vorlage.csv', GENERIC_HEADER + '\n', 'text/csv'));
$('dl-backup').addEventListener('click', () => download('cointracker-backup.json', exportJson(txs), 'application/json'));
$('dl-report').addEventListener('click', () => {
  const y = Number($('year').value);
  const rows = yearSummary(computeFifo(txs), y).disposals.map(d => ({
    verkauf: d.soldAt.slice(0, 10), anschaffung: d.acquiredAt.slice(0, 10), asset: d.asset, menge: d.amount,
    erloes: d.proceeds.toFixed(2), kosten: d.cost.toFixed(2), gewinn: d.gain.toFixed(2),
    status: d.taxFree ? 'steuerfrei' : 'steuerpflichtig',
  }));
  download(`bericht-${y}.csv`, toCsv(rows, ['verkauf', 'anschaffung', 'asset', 'menge', 'erloes', 'kosten', 'gewinn', 'status']), 'text/csv');
});

render();
