export function getOrCreateDevice(db, { manufacturerId, deviceType, model, inventoryNumber, serialNumber, location, nextMaintenanceDue, defaultDurationMinutes }) {
  const existing = db
    .prepare('SELECT * FROM devices WHERE manufacturer_id = ? AND inventory_number = ?')
    .get(manufacturerId, inventoryNumber);
  if (existing) {
    db.prepare(
      `UPDATE devices SET device_type = ?, model = ?, serial_number = ?, location = ?,
         next_maintenance_due = ?, default_duration_minutes = COALESCE(?, default_duration_minutes)
       WHERE id = ?`
    ).run(
      deviceType,
      model ?? null,
      serialNumber ?? null,
      location ?? null,
      nextMaintenanceDue ?? null,
      defaultDurationMinutes ?? null,
      existing.id
    );
    return db.prepare('SELECT * FROM devices WHERE id = ?').get(existing.id);
  }
  const { lastInsertRowid } = db
    .prepare(
      `INSERT INTO devices
         (manufacturer_id, device_type, model, inventory_number, serial_number, location,
          next_maintenance_due, default_duration_minutes)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
    )
    .run(
      manufacturerId,
      deviceType,
      model ?? null,
      inventoryNumber,
      serialNumber ?? null,
      location ?? null,
      nextMaintenanceDue ?? null,
      defaultDurationMinutes ?? null
    );
  return db.prepare('SELECT * FROM devices WHERE id = ?').get(lastInsertRowid);
}

export function getDevice(db, id) {
  return db.prepare('SELECT * FROM devices WHERE id = ?').get(id);
}

export function listDevicesByManufacturer(db, manufacturerId) {
  return db
    .prepare('SELECT * FROM devices WHERE manufacturer_id = ? ORDER BY device_type, inventory_number')
    .all(manufacturerId);
}
