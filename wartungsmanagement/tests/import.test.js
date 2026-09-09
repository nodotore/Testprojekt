import test from 'node:test';
import assert from 'node:assert/strict';
import { setupDb } from './helpers.js';
import { buildSampleWorkbook } from '../fixtures/build-sample-devices.js';
import { importDevicesFromExcel } from '../src/import/excelImport.js';
import { groupOpenOrdersByManufacturer, buildRequestFromGroup } from '../src/grouping/groupByManufacturer.js';
import { getMaintenanceRequestWithOrders } from '../src/models/maintenanceRequests.js';

test('Milestone 1: Excel-Import legt Hersteller, Geräte und je Gerät einen eigenen Wartungsauftrag an', async () => {
  const db = setupDb();
  const path = await buildSampleWorkbook('/tmp/wm-test-sample.xlsx');
  const { devices, orders } = await importDevicesFromExcel(db, path);

  assert.equal(devices.length, 5);
  assert.equal(orders.length, 5);
  assert.equal(new Set(orders.map((o) => o.order_number)).size, 5, 'jeder Auftrag hat eine eigene, eindeutige Nummer');
});

test('Milestone 2: Gruppierung nach Hersteller, jedes Gerät bleibt ein eigener Auftrag', async () => {
  const db = setupDb();
  const path = await buildSampleWorkbook('/tmp/wm-test-sample.xlsx');
  await importDevicesFromExcel(db, path);

  const groups = groupOpenOrdersByManufacturer(db);
  const fresenius = groups.find((g) => g.manufacturer.name === 'Fresenius');
  assert.ok(fresenius, 'Fresenius-Gruppe vorhanden');
  assert.equal(fresenius.openOrders.length, 3);
  assert.deepEqual(
    fresenius.openOrders.map((o) => o.inventory_number).sort(),
    ['MT-1001', 'MT-1002', 'MT-2050']
  );
});

test('mehrere Geräte in einer gemeinsamen Wartungsanfrage, aber getrennte Wartungsaufträge', async () => {
  const db = setupDb();
  const path = await buildSampleWorkbook('/tmp/wm-test-sample.xlsx');
  const { orders } = await importDevicesFromExcel(db, path);
  const freseniusOrders = orders.filter((o) => o.order_number && o.manufacturer_id === orders[0].manufacturer_id);
  const orderIds = freseniusOrders.slice(0, 3).map((o) => o.id);

  const request = buildRequestFromGroup(db, {
    manufacturerId: orders[0].manufacturer_id,
    orderIds,
    emailThreadId: 'thread-1',
  });

  assert.equal(request.orders.length, 3);
  const reloaded = getMaintenanceRequestWithOrders(db, request.id);
  assert.equal(reloaded.orders.length, 3);
  assert.equal(new Set(reloaded.orders.map((o) => o.id)).size, 3, 'jedes Gerät bleibt sein eigener Wartungsauftrag');
});
