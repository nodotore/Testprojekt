import ExcelJS from 'exceljs';
import { getOrCreateManufacturer } from '../models/manufacturers.js';
import { getOrCreateDevice } from '../models/devices.js';
import { createMaintenanceOrder } from '../models/maintenanceOrders.js';
import { parseGermanDate } from '../util/germanDates.js';

// Erwartete Spaltenüberschriften (Zeile 1), Groß-/Kleinschreibung egal.
const COLUMN_ALIASES = {
  hersteller: 'manufacturer',
  gerätetyp: 'deviceType',
  geraetetyp: 'deviceType',
  gerät: 'model',
  geraet: 'model',
  modell: 'model',
  inventarnummer: 'inventoryNumber',
  seriennummer: 'serialNumber',
  standort: 'location',
  'wartung fällig': 'nextMaintenanceDue',
  'wartung faellig': 'nextMaintenanceDue',
};

/**
 * Milestone 1: Liest Geräte aus einer Excel-Datei ein. Legt je Zeile
 * Hersteller (falls neu), Gerät und einen eigenen Wartungsauftrag an.
 * @param {import('node:sqlite').DatabaseSync} db
 * @param {string} filePath
 * @returns {Promise<{devices: object[], orders: object[]}>}
 */
export async function importDevicesFromExcel(db, filePath) {
  const workbook = new ExcelJS.Workbook();
  await workbook.xlsx.readFile(filePath);
  const sheet = workbook.worksheets[0];
  if (!sheet) throw new Error('Excel-Datei enthält kein Arbeitsblatt.');

  const headerRow = sheet.getRow(1);
  const columnIndexByField = {};
  headerRow.eachCell((cell, colNumber) => {
    const key = String(cell.value ?? '').trim().toLowerCase();
    const field = COLUMN_ALIASES[key];
    if (field) columnIndexByField[field] = colNumber;
  });
  const required = ['manufacturer', 'deviceType', 'inventoryNumber'];
  for (const field of required) {
    if (!columnIndexByField[field]) {
      throw new Error(`Excel-Import: Pflichtspalte für "${field}" nicht gefunden.`);
    }
  }

  const devices = [];
  const orders = [];
  sheet.eachRow((row, rowNumber) => {
    if (rowNumber === 1) return;
    const get = (field) => {
      const idx = columnIndexByField[field];
      if (!idx) return null;
      const cell = row.getCell(idx);
      return cell.value == null ? null : cell.value;
    };
    const manufacturerName = String(get('manufacturer') ?? '').trim();
    const inventoryNumber = String(get('inventoryNumber') ?? '').trim();
    if (!manufacturerName || !inventoryNumber) return;

    const manufacturer = getOrCreateManufacturer(db, manufacturerName);
    const dueDate = parseGermanDate(get('nextMaintenanceDue'));
    const device = getOrCreateDevice(db, {
      manufacturerId: manufacturer.id,
      deviceType: String(get('deviceType') ?? '').trim(),
      model: get('model') ? String(get('model')).trim() : null,
      inventoryNumber,
      serialNumber: get('serialNumber') ? String(get('serialNumber')).trim() : null,
      location: get('location') ? String(get('location')).trim() : null,
      nextMaintenanceDue: dueDate,
    });
    devices.push(device);

    const order = createMaintenanceOrder(db, {
      deviceId: device.id,
      manufacturerId: manufacturer.id,
      dueDate,
    });
    orders.push(order);
  });

  return { devices, orders };
}
