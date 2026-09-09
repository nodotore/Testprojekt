import test from 'node:test';
import assert from 'node:assert/strict';
import { extractAppointmentProposals } from '../src/nlp/appointmentExtractor.js';

test('Milestone 7/8: mehrere Terminvorschläge ohne Uhrzeit in einer Nachricht', () => {
  const text = 'Wir könnten am 15.09., 18.09. oder 22.09.2026 kommen.';
  const result = extractAppointmentProposals(text, []);
  assert.deepEqual(
    result.map((r) => r.date),
    ['2026-09-15', '2026-09-18', '2026-09-22']
  );
});

test('Milestone 7/8: mehrere Terminvorschläge mit Uhrzeit', () => {
  const text =
    'Wir könnten am 15.09.2026 – 08:00 Uhr, 18.09.2026 – 10:30 Uhr oder 22.09.2026 – 13:00 Uhr kommen.';
  const result = extractAppointmentProposals(text, []);
  assert.deepEqual(result, [
    { orderIds: [], date: '2026-09-15', startTime: '08:00', proposedDurationMinutes: null },
    { orderIds: [], date: '2026-09-18', startTime: '10:30', proposedDurationMinutes: null },
    { orderIds: [], date: '2026-09-22', startTime: '13:00', proposedDurationMinutes: null },
  ]);
});

test('mehrere Geräte an einem gemeinsamen Termin', () => {
  const orders = [1, 2, 3, 4, 5].map((i) => ({ orderId: i, inventoryNumber: `MT-100${i}` }));
  const text = 'Wir kommen am 18.09.2026 und warten alle fünf Geräte.';
  const result = extractAppointmentProposals(text, orders);
  assert.equal(result.length, 1);
  assert.deepEqual(result[0].orderIds, [1, 2, 3, 4, 5]);
  assert.equal(result[0].date, '2026-09-18');
});

test('unterschiedliche Termine pro Gerät', () => {
  const orders = [
    { orderId: 1, inventoryNumber: 'MT-1001' },
    { orderId: 2, inventoryNumber: 'MT-1002' },
    { orderId: 3, inventoryNumber: 'MT-1003' },
  ];
  const text =
    'Gerät MT-1001 können wir am 18.09. warten. Gerät MT-1002 am 21.09. Gerät MT-1003 wäre am 25.09. möglich.';
  const result = extractAppointmentProposals(text, orders, { defaultYear: 2026 });
  assert.deepEqual(
    result.map((r) => [r.orderIds, r.date]),
    [
      [[1], '2026-09-18'],
      [[2], '2026-09-21'],
      [[3], '2026-09-25'],
    ]
  );
});

test('mehrere Alternativen pro Gerät', () => {
  const orders = [
    { orderId: 1, inventoryNumber: 'MT-1001' },
    { orderId: 2, inventoryNumber: 'MT-1002' },
  ];
  const text = 'Gerät MT-1001: 18.09.2026, 21.09.2026, 25.09.2026. Gerät MT-1002: 22.09.2026, 23.09.2026.';
  const result = extractAppointmentProposals(text, orders);
  const forDevice1 = result.filter((r) => r.orderIds[0] === 1);
  const forDevice2 = result.filter((r) => r.orderIds[0] === 2);
  assert.deepEqual(forDevice1.map((r) => r.date), ['2026-09-18', '2026-09-21', '2026-09-25']);
  assert.deepEqual(forDevice2.map((r) => r.date), ['2026-09-22', '2026-09-23']);
});

test('Termindauer wird aus dem Text erkannt', () => {
  const text = 'Wir kommen am 18.09.2026 (ca. 2 Stunden) und warten alle Geräte.';
  const result = extractAppointmentProposals(text, []);
  assert.equal(result[0].proposedDurationMinutes, 120);
});
