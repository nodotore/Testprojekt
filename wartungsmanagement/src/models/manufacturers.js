export function getOrCreateManufacturer(db, name, contactEmail = null) {
  const existing = db.prepare('SELECT * FROM manufacturers WHERE name = ?').get(name);
  if (existing) return existing;
  const { lastInsertRowid } = db
    .prepare('INSERT INTO manufacturers (name, contact_email) VALUES (?, ?)')
    .run(name, contactEmail);
  return db.prepare('SELECT * FROM manufacturers WHERE id = ?').get(lastInsertRowid);
}

export function getManufacturer(db, id) {
  return db.prepare('SELECT * FROM manufacturers WHERE id = ?').get(id);
}

export function listManufacturers(db) {
  return db.prepare('SELECT * FROM manufacturers ORDER BY name').all();
}
