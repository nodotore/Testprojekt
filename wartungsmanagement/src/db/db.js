import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SCHEMA_SQL = readFileSync(join(__dirname, 'schema.sql'), 'utf8');

// Standarddauern je Gerätetyp (siehe README/Anforderung "Termindauer").
const DEFAULT_DEVICE_TYPE_DURATIONS = [
  ['Dialysegerät', 120],
  ['Patientenmonitor', 60],
  ['Defibrillator', 90],
];

/**
 * Öffnet eine Wartungsmanagement-Datenbank (Datei oder ':memory:') und legt
 * das Schema an, falls es noch nicht existiert.
 * @param {string} [location] Pfad zur SQLite-Datei, Standard ':memory:'
 * @returns {DatabaseSync}
 */
export function openDatabase(location = ':memory:') {
  const db = new DatabaseSync(location);
  db.exec(SCHEMA_SQL);
  seedDeviceTypeDefaults(db);
  return db;
}

function seedDeviceTypeDefaults(db) {
  const insert = db.prepare(
    `INSERT OR IGNORE INTO device_type_defaults (device_type, default_duration_minutes)
     VALUES (?, ?)`
  );
  for (const [type, minutes] of DEFAULT_DEVICE_TYPE_DURATIONS) {
    insert.run(type, minutes);
  }
}

export function nowIso() {
  return new Date().toISOString();
}
