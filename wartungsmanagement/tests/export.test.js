import test from 'node:test';
import assert from 'node:assert/strict';
import { setupDb, seedFreseniusExample } from './helpers.js';
import { createAppointmentProposal, updateProposalStatus } from '../src/models/appointmentProposals.js';
import { ProposalStatus } from '../src/constants/status.js';
import { confirmAppointment } from '../src/workflow/confirmAppointment.js';
import { MockCalendarClient } from '../src/outlook/mockCalendarClient.js';
import { buildRows, exportAppointmentOverview } from '../src/export/excelExport.js';
import { proposalSummary } from '../src/dashboard/dashboardSummary.js';
import ExcelJS from 'exceljs';

test('Milestone 13: Excel-Zeile enthält Terminvorschläge, gewählten Termin und Status', async () => {
  const db = setupDb();
  const { manufacturer, orders } = seedFreseniusExample(db);
  const order = orders[0];
  createAppointmentProposal(db, { manufacturerId: manufacturer.id, orderIds: [order.id], proposalDate: '2026-09-15' });
  const chosen = createAppointmentProposal(db, {
    manufacturerId: manufacturer.id,
    orderIds: [order.id],
    proposalDate: '2026-09-18',
    startTime: '09:00',
  });
  createAppointmentProposal(db, { manufacturerId: manufacturer.id, orderIds: [order.id], proposalDate: '2026-09-22' });
  updateProposalStatus(db, chosen.id, ProposalStatus.FREI);
  await confirmAppointment(db, new MockCalendarClient(), chosen.id);

  const rows = buildRows(db);
  const row = rows.find((r) => r[2] === 'MT-1001');
  assert.deepEqual(row.slice(0, 3), ['Fresenius', 'Dialysegerät 5008 CorDiax', 'MT-1001']);
  assert.equal(row[3], '15.09 / 18.09 / 22.09');
  assert.equal(row[4], '18.09.2026 09:00');
  assert.equal(row[7], 'Bestätigt');
});

test('Excel-Datei lässt sich schreiben und wieder einlesen', async () => {
  const db = setupDb();
  seedFreseniusExample(db);
  const path = '/tmp/wm-test-export.xlsx';
  await exportAppointmentOverview(db, path);

  const workbook = new ExcelJS.Workbook();
  await workbook.xlsx.readFile(path);
  const sheet = workbook.worksheets[0];
  assert.equal(sheet.getRow(1).getCell(1).value, 'Hersteller');
  assert.equal(sheet.rowCount, 4); // Kopfzeile + 3 Geräte
});

test('Dashboard-Kennzahlen zählen Terminvorschläge nach Status', () => {
  const db = setupDb();
  const { manufacturer, orders } = seedFreseniusExample(db);
  const ids = [
    createAppointmentProposal(db, { manufacturerId: manufacturer.id, orderIds: [orders[0].id], proposalDate: '2026-09-15' }).id,
    createAppointmentProposal(db, { manufacturerId: manufacturer.id, orderIds: [orders[1].id], proposalDate: '2026-09-16' }).id,
    createAppointmentProposal(db, { manufacturerId: manufacturer.id, orderIds: [orders[2].id], proposalDate: '2026-09-17' }).id,
  ];
  updateProposalStatus(db, ids[0], ProposalStatus.FREI);
  updateProposalStatus(db, ids[1], ProposalStatus.BELEGT);
  updateProposalStatus(db, ids[2], ProposalStatus.MANUELLE_PRUEFUNG);

  const summary = proposalSummary(db);
  assert.equal(summary.frei, 1);
  assert.equal(summary.belegt, 1);
  assert.equal(summary.manuellePruefung, 1);
  assert.equal(summary.total, 3);
});
