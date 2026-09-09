import test from 'node:test';
import assert from 'node:assert/strict';
import { setupDb, seedFreseniusExample } from './helpers.js';
import { createAppointmentProposal, getAppointmentProposal, updateProposalStatus } from '../src/models/appointmentProposals.js';
import { ProposalStatus, OrderStatus } from '../src/constants/status.js';
import { confirmAppointment } from '../src/workflow/confirmAppointment.js';
import { proposeReschedule, confirmReschedule } from '../src/workflow/rescheduleAppointment.js';
import { cancelAppointment, deleteOutlookEvent } from '../src/workflow/cancelAppointment.js';
import { MockCalendarClient } from '../src/outlook/mockCalendarClient.js';
import { getMaintenanceOrder } from '../src/models/maintenanceOrders.js';

test('Milestone 12: Bestätigung legt einen gemeinsamen Outlook-Termin für mehrere Geräte an', async () => {
  const db = setupDb();
  const { manufacturer, orders } = seedFreseniusExample(db);
  const calendarClient = new MockCalendarClient();
  const proposal = createAppointmentProposal(db, {
    manufacturerId: manufacturer.id,
    orderIds: [orders[0].id, orders[1].id],
    proposalDate: '2026-09-18',
    startTime: '08:00',
  });
  updateProposalStatus(db, proposal.id, ProposalStatus.FREI);

  const confirmed = await confirmAppointment(db, calendarClient, proposal.id, { technician: 'Herr Müller' });
  assert.equal(confirmed.status, ProposalStatus.BESTAETIGT);
  assert.ok(confirmed.outlook_event_id);

  const event = await calendarClient.getEvent(confirmed.outlook_event_id);
  assert.equal(event.subject, 'Wartung – Fresenius – 2 Geräte');
  assert.match(event.body, /WA-2026-00101/);
  assert.match(event.body, /WA-2026-00102/);

  assert.equal(getMaintenanceOrder(db, orders[0].id).status, OrderStatus.TERMIN_BESTAETIGT);
  assert.equal(getMaintenanceOrder(db, orders[1].id).status, OrderStatus.TERMIN_BESTAETIGT);
});

test('Terminverschiebung aktualisiert den bestehenden Outlook-Termin statt einen zweiten anzulegen', async () => {
  const db = setupDb();
  const { manufacturer, orders } = seedFreseniusExample(db);
  const calendarClient = new MockCalendarClient();
  const proposal = createAppointmentProposal(db, {
    manufacturerId: manufacturer.id,
    orderIds: [orders[0].id],
    proposalDate: '2026-09-18',
    startTime: '08:00',
  });
  updateProposalStatus(db, proposal.id, ProposalStatus.FREI);
  const confirmed = await confirmAppointment(db, calendarClient, proposal.id);

  const { newProposal } = proposeReschedule(db, proposal.id, { proposalDate: '2026-09-22', startTime: '08:00' });
  updateProposalStatus(db, newProposal.id, ProposalStatus.FREI);
  const rescheduled = await confirmReschedule(db, calendarClient, {
    oldProposalId: proposal.id,
    newProposalId: newProposal.id,
  });

  assert.equal(rescheduled.outlook_event_id, confirmed.outlook_event_id, 'derselbe Outlook-Termin wird verändert');
  assert.equal(calendarClient.events.size, 1, 'kein zweiter Outlook-Termin entsteht');
  assert.equal(getAppointmentProposal(db, proposal.id).status, ProposalStatus.VERSCHOBEN);

  const event = await calendarClient.getEvent(rescheduled.outlook_event_id);
  assert.match(event.start, /2026-09-22/);
});

test('Absage markiert den Outlook-Termin, löscht ihn aber nicht automatisch', async () => {
  const db = setupDb();
  const { manufacturer, orders } = seedFreseniusExample(db);
  const calendarClient = new MockCalendarClient();
  const proposal = createAppointmentProposal(db, {
    manufacturerId: manufacturer.id,
    orderIds: [orders[0].id],
    proposalDate: '2026-09-18',
    startTime: '08:00',
  });
  updateProposalStatus(db, proposal.id, ProposalStatus.FREI);
  const confirmed = await confirmAppointment(db, calendarClient, proposal.id);

  const result = await cancelAppointment(db, calendarClient, confirmed.id, { note: 'Hersteller sagt ab' });
  assert.equal(result.proposal.status, ProposalStatus.ABSAGE_ERHALTEN);
  assert.equal(result.requiresUserDecision, true);
  assert.equal(result.userPrompt, 'Kalendertermin löschen?');

  const stillThere = await calendarClient.getEvent(confirmed.outlook_event_id);
  assert.ok(stillThere, 'Termin wird nur markiert, nicht automatisch gelöscht');
  assert.match(stillThere.subject, /^\[ABGESAGT\]/);
  assert.equal(getMaintenanceOrder(db, orders[0].id).status, OrderStatus.OFFEN);

  await deleteOutlookEvent(db, calendarClient, confirmed.id);
  assert.equal(await calendarClient.getEvent(confirmed.outlook_event_id), null);
});
