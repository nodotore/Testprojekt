import { OrderStatus } from '../constants/status.js';

const ORDER_NUMBER_PREFIX = 'WA';
const ORDER_NUMBER_START = 101;

/**
 * Erzeugt die nächste fortlaufende Wartungsauftragsnummer für ein Jahr,
 * z. B. "WA-2026-00101".
 */
export function nextOrderNumber(db, year) {
  const like = `${ORDER_NUMBER_PREFIX}-${year}-%`;
  const rows = db
    .prepare('SELECT order_number FROM maintenance_orders WHERE order_number LIKE ?')
    .all(like);
  let maxSeq = ORDER_NUMBER_START - 1;
  for (const row of rows) {
    const seq = Number.parseInt(row.order_number.split('-')[2], 10);
    if (Number.isFinite(seq) && seq > maxSeq) maxSeq = seq;
  }
  const next = maxSeq + 1;
  return `${ORDER_NUMBER_PREFIX}-${year}-${String(next).padStart(5, '0')}`;
}

/**
 * Legt für ein Gerät einen eigenen Wartungsauftrag an (1 Auftrag = 1 Gerät),
 * auch wenn mehrere Geräte gemeinsam in einer Wartungsanfrage stehen.
 */
export function createMaintenanceOrder(db, { deviceId, manufacturerId, dueDate, requestId = null, year = new Date().getFullYear() }) {
  const orderNumber = nextOrderNumber(db, year);
  const { lastInsertRowid } = db
    .prepare(
      `INSERT INTO maintenance_orders (order_number, device_id, manufacturer_id, request_id, status, due_date)
       VALUES (?, ?, ?, ?, ?, ?)`
    )
    .run(orderNumber, deviceId, manufacturerId, requestId, OrderStatus.OFFEN, dueDate ?? null);
  return db.prepare('SELECT * FROM maintenance_orders WHERE id = ?').get(lastInsertRowid);
}

export function getMaintenanceOrder(db, id) {
  return db.prepare('SELECT * FROM maintenance_orders WHERE id = ?').get(id);
}

export function listOpenOrdersByManufacturer(db, manufacturerId) {
  return db
    .prepare(
      `SELECT mo.*, d.device_type, d.model, d.inventory_number, d.serial_number, d.next_maintenance_due
       FROM maintenance_orders mo
       JOIN devices d ON d.id = mo.device_id
       WHERE mo.manufacturer_id = ? AND mo.status = ?
       ORDER BY mo.due_date`
    )
    .all(manufacturerId, OrderStatus.OFFEN);
}

export function listAllOrdersWithDevice(db) {
  return db
    .prepare(
      `SELECT mo.*, d.device_type, d.model, d.inventory_number, d.serial_number,
              m.name AS manufacturer_name
       FROM maintenance_orders mo
       JOIN devices d ON d.id = mo.device_id
       JOIN manufacturers m ON m.id = mo.manufacturer_id
       ORDER BY m.name, d.device_type, d.inventory_number`
    )
    .all();
}

export function setOrderStatus(db, orderId, status) {
  db.prepare('UPDATE maintenance_orders SET status = ? WHERE id = ?').run(status, orderId);
}

export function assignOrdersToRequest(db, orderIds, requestId) {
  const stmt = db.prepare('UPDATE maintenance_orders SET request_id = ? WHERE id = ?');
  for (const orderId of orderIds) stmt.run(requestId, orderId);
}
