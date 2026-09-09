import test from 'node:test';
import assert from 'node:assert/strict';
import { setupDb } from './helpers.js';
import { getOrCreateManufacturer } from '../src/models/manufacturers.js';
import { getOrCreateDevice } from '../src/models/devices.js';
import { createMaintenanceOrder } from '../src/models/maintenanceOrders.js';
import { createAppointmentProposal, getAppointmentProposal, updateProposalStatus } from '../src/models/appointmentProposals.js';
import { ProposalStatus } from '../src/constants/status.js';
import { recommendSchedule } from '../src/recommendation/recommend.js';

test('Milestone 10: bevorzugt den Termin, an dem alle Geräte gemeinsam gewartet werden können', () => {
  const db = setupDb();
  const manufacturer = getOrCreateManufacturer(db, 'Fresenius');
  const devices = ['MT-1001', 'MT-1002', 'MT-1003'].map((inv) =>
    getOrCreateDevice(db, { manufacturerId: manufacturer.id, deviceType: 'Dialysegerät', inventoryNumber: inv })
  );
  const orders = devices.map((d) =>
    createMaintenanceOrder(db, { deviceId: d.id, manufacturerId: manufacturer.id, dueDate: '2026-09-30' })
  );

  const proposalIds = [
    createAppointmentProposal(db, { manufacturerId: manufacturer.id, orderIds: [orders[0].id], proposalDate: '2026-09-14' }).id, // Montag
    createAppointmentProposal(db, { manufacturerId: manufacturer.id, orderIds: [orders[0].id], proposalDate: '2026-09-17' }).id, // Donnerstag
    createAppointmentProposal(db, { manufacturerId: manufacturer.id, orderIds: [orders[1].id], proposalDate: '2026-09-15' }).id, // Dienstag
    createAppointmentProposal(db, { manufacturerId: manufacturer.id, orderIds: [orders[1].id], proposalDate: '2026-09-17' }).id, // Donnerstag
    createAppointmentProposal(db, { manufacturerId: manufacturer.id, orderIds: [orders[2].id], proposalDate: '2026-09-17' }).id, // Donnerstag
  ];
  for (const id of proposalIds) updateProposalStatus(db, id, ProposalStatus.FREI);
  const proposals = proposalIds.map((id) => getAppointmentProposal(db, id));

  const { recommended, uncoveredOrderIds } = recommendSchedule(db, {
    orderIds: orders.map((o) => o.id),
    proposals,
  });

  assert.equal(recommended.length, 1, 'ein gemeinsamer Termin statt drei einzelner reicht aus');
  assert.equal(recommended[0].date, '2026-09-17');
  assert.equal(recommended[0].coveredCount, 3);
  assert.deepEqual(uncoveredOrderIds, []);
});

test('Termin nach der Fälligkeit wird gegenüber einem rechtzeitigen Termin niedriger priorisiert', () => {
  const db = setupDb();
  const manufacturer = getOrCreateManufacturer(db, 'Firma A');
  const device = getOrCreateDevice(db, { manufacturerId: manufacturer.id, deviceType: 'Patientenmonitor', inventoryNumber: 'INV-1' });
  const order = createMaintenanceOrder(db, { deviceId: device.id, manufacturerId: manufacturer.id, dueDate: '2026-09-20' });

  const late = createAppointmentProposal(db, { manufacturerId: manufacturer.id, orderIds: [order.id], proposalDate: '2026-09-25' });
  const onTime = createAppointmentProposal(db, { manufacturerId: manufacturer.id, orderIds: [order.id], proposalDate: '2026-09-18' });
  updateProposalStatus(db, late.id, ProposalStatus.FREI);
  updateProposalStatus(db, onTime.id, ProposalStatus.FREI);

  const proposals = [late, onTime].map((p) => getAppointmentProposal(db, p.id));
  const { recommended } = recommendSchedule(db, { orderIds: [order.id], proposals });
  assert.equal(recommended[0].date, '2026-09-18');
});
