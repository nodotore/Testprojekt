import test from 'node:test';
import assert from 'node:assert/strict';
import { setupDb, seedFreseniusExample } from './helpers.js';
import { createAppointmentProposal, getAppointmentProposal } from '../src/models/appointmentProposals.js';
import { checkAllProposals } from '../src/outlook/availabilityCheck.js';
import { MockCalendarClient } from '../src/outlook/mockCalendarClient.js';
import { ProposalStatus } from '../src/constants/status.js';

test('Milestone 9: Outlook-Verfügbarkeitsprüfung erkennt belegt/frei aus dem Lastenheft-Beispiel', async () => {
  const db = setupDb();
  const { manufacturer, orders } = seedFreseniusExample(db);
  const order = orders[0]; // Dialysegerät, 2h Standarddauer

  const dates = [
    ['2026-09-15', '09:00'],
    ['2026-09-16', '09:00'],
    ['2026-09-18', '13:00'],
  ];
  const created = dates.map(([date, time]) =>
    createAppointmentProposal(db, {
      manufacturerId: manufacturer.id,
      orderIds: [order.id],
      proposalDate: date,
      startTime: time,
    })
  );

  const calendarClient = new MockCalendarClient();
  calendarClient.addBusyBlock(
    new Date('2026-09-15T09:00:00').toISOString(),
    new Date('2026-09-15T11:00:00').toISOString(),
    'Anderer Termin'
  );

  const proposals = created.map((p) => getAppointmentProposal(db, p.id));
  const results = await checkAllProposals(db, calendarClient, proposals);

  assert.equal(results[0].status, ProposalStatus.BELEGT);
  assert.equal(results[1].status, ProposalStatus.FREI);
  assert.equal(results[2].status, ProposalStatus.FREI);
});

test('Termin außerhalb der Arbeitszeit erfordert manuelle Prüfung, ohne Outlook-Aufruf', async () => {
  const db = setupDb();
  const { manufacturer, orders } = seedFreseniusExample(db);
  const proposal = createAppointmentProposal(db, {
    manufacturerId: manufacturer.id,
    orderIds: [orders[0].id],
    proposalDate: '2026-09-15',
    startTime: '19:00',
  });

  let called = false;
  const calendarClient = {
    async getFreeBusy() {
      called = true;
      return { status: 'FREI', conflicts: [] };
    },
  };

  const [result] = await checkAllProposals(db, calendarClient, [getAppointmentProposal(db, proposal.id)]);
  assert.equal(result.status, ProposalStatus.MANUELLE_PRUEFUNG);
  assert.equal(result.outlook_status, 'AUSSERHALB_ARBEITSZEIT');
  assert.equal(called, false);
});

test('fehlende Dauer (unbekannter Gerätetyp, keine Angabe) -> manuelle Prüfung', async () => {
  const db = setupDb();
  const { manufacturer } = seedFreseniusExample(db);
  const { getOrCreateDevice } = await import('../src/models/devices.js');
  const { createMaintenanceOrder } = await import('../src/models/maintenanceOrders.js');
  const device = getOrCreateDevice(db, {
    manufacturerId: manufacturer.id,
    deviceType: 'Ultraschallgerät',
    inventoryNumber: 'US-1',
  });
  const order = createMaintenanceOrder(db, { deviceId: device.id, manufacturerId: manufacturer.id });
  const proposal = createAppointmentProposal(db, {
    manufacturerId: manufacturer.id,
    orderIds: [order.id],
    proposalDate: '2026-09-15',
    startTime: '09:00',
  });

  const [result] = await checkAllProposals(db, new MockCalendarClient(), [
    getAppointmentProposal(db, proposal.id),
  ]);
  assert.equal(result.status, ProposalStatus.MANUELLE_PRUEFUNG);
  assert.match(result.remark, /Dauer unbekannt/);
});
