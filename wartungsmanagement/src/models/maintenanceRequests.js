import { assignOrdersToRequest } from './maintenanceOrders.js';

/**
 * Bündelt mehrere offene Wartungsaufträge desselben Herstellers zu einer
 * gemeinsamen Wartungsanfrage (eine E-Mail, mehrere Geräte). Jeder Auftrag
 * bleibt dabei ein eigener, separat verfolgbarer Wartungsauftrag.
 */
export function createMaintenanceRequest(db, { manufacturerId, orderIds, emailThreadId = null }) {
  if (!orderIds || orderIds.length === 0) {
    throw new Error('Eine Wartungsanfrage benötigt mindestens einen Wartungsauftrag.');
  }
  const { lastInsertRowid } = db
    .prepare('INSERT INTO maintenance_requests (manufacturer_id, email_thread_id) VALUES (?, ?)')
    .run(manufacturerId, emailThreadId);
  assignOrdersToRequest(db, orderIds, lastInsertRowid);
  return getMaintenanceRequestWithOrders(db, lastInsertRowid);
}

export function getMaintenanceRequestWithOrders(db, requestId) {
  const request = db.prepare('SELECT * FROM maintenance_requests WHERE id = ?').get(requestId);
  if (!request) return null;
  const orders = db
    .prepare(
      `SELECT mo.*, d.device_type, d.model, d.inventory_number, d.serial_number
       FROM maintenance_orders mo
       JOIN devices d ON d.id = mo.device_id
       WHERE mo.request_id = ?
       ORDER BY d.device_type, d.inventory_number`
    )
    .all(requestId);
  return { ...request, orders };
}
