-- Wartungsmanagement Datenmodell
--
-- Verbindliche Beziehungsregel (siehe README.md):
--   Ein Hersteller            -> viele Geräte
--   Eine Wartungsanfrage      -> mehrere Wartungsaufträge (= mehrere Geräte)
--   Ein Wartungsauftrag       -> genau ein Gerät
--   Ein Gerät                 -> mehrere Terminvorschläge (über die Zeit)
--   Ein Terminvorschlag       -> ein oder mehrere Wartungsaufträge/Geräte (M:N)
--   Ein bestätigter Termin    -> mehrere Geräte möglich (folgt aus dem M:N oben)
--   Ein Outlook-Termin        -> mehrere Wartungsaufträge möglich (folgt aus dem M:N oben)
--
-- Die M:N-Beziehung zwischen Terminvorschlag und Wartungsauftrag wird über
-- die Join-Tabelle appointment_proposal_orders abgebildet. Ein einzelner
-- Outlook-Kalendereintrag entspricht genau einem bestätigten Terminvorschlag;
-- da dieser bereits mit mehreren Wartungsaufträgen verknüpft sein kann, ist
-- "ein Outlook-Termin -> mehrere Wartungsaufträge" damit automatisch erfüllt,
-- ohne eine weitere eigene Tabelle dafür zu benötigen.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS manufacturers (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  name          TEXT NOT NULL UNIQUE,
  contact_email TEXT,
  created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS devices (
  id                       INTEGER PRIMARY KEY AUTOINCREMENT,
  manufacturer_id          INTEGER NOT NULL REFERENCES manufacturers(id),
  device_type              TEXT NOT NULL,
  model                    TEXT,
  inventory_number         TEXT NOT NULL,
  serial_number            TEXT,
  location                 TEXT,
  next_maintenance_due     TEXT,
  default_duration_minutes INTEGER,
  created_at               TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  UNIQUE (manufacturer_id, inventory_number)
);

CREATE INDEX IF NOT EXISTS idx_devices_manufacturer ON devices(manufacturer_id);

-- Standarddauer je Gerätetyp, verwendet wenn ein Gerät selbst keine eigene hat.
CREATE TABLE IF NOT EXISTS device_type_defaults (
  device_type               TEXT PRIMARY KEY,
  default_duration_minutes  INTEGER NOT NULL
);

-- Eine Wartungsanfrage bündelt mehrere Wartungsaufträge, die gemeinsam in
-- einer E-Mail an den Hersteller angefragt wurden (Milestone 2).
CREATE TABLE IF NOT EXISTS maintenance_requests (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  manufacturer_id INTEGER NOT NULL REFERENCES manufacturers(id),
  email_thread_id TEXT,
  created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Ein Wartungsauftrag gehört zu genau einem Gerät, kann aber Teil einer
-- gemeinsamen Wartungsanfrage sein (request_id ist optional/nullable, bis
-- der Auftrag einer Anfrage zugeordnet wird).
CREATE TABLE IF NOT EXISTS maintenance_orders (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  order_number    TEXT NOT NULL UNIQUE,
  device_id       INTEGER NOT NULL REFERENCES devices(id),
  manufacturer_id INTEGER NOT NULL REFERENCES manufacturers(id),
  request_id      INTEGER REFERENCES maintenance_requests(id),
  status          TEXT NOT NULL DEFAULT 'OFFEN',
  due_date        TEXT,
  created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_orders_device ON maintenance_orders(device_id);
CREATE INDEX IF NOT EXISTS idx_orders_manufacturer ON maintenance_orders(manufacturer_id);
CREATE INDEX IF NOT EXISTS idx_orders_request ON maintenance_orders(request_id);

-- Ein Terminvorschlag stammt von genau einem Hersteller (aus einer E-Mail),
-- kann sich aber auf ein oder mehrere Wartungsaufträge/Geräte beziehen.
CREATE TABLE IF NOT EXISTS appointment_proposals (
  id                        INTEGER PRIMARY KEY AUTOINCREMENT,
  manufacturer_id           INTEGER NOT NULL REFERENCES manufacturers(id),
  proposal_date             TEXT NOT NULL,
  start_time                TEXT,
  end_time                  TEXT,
  proposed_duration_minutes INTEGER,
  duration_source           TEXT,
  source_email_id           TEXT,
  outlook_status            TEXT NOT NULL DEFAULT 'UNGEPRUEFT',
  status                    TEXT NOT NULL DEFAULT 'NEU',
  remark                    TEXT,
  outlook_event_id          TEXT,
  outlook_event_start       TEXT,
  outlook_event_end         TEXT,
  superseded_by_proposal_id INTEGER REFERENCES appointment_proposals(id),
  created_at                TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_at                TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_proposals_manufacturer ON appointment_proposals(manufacturer_id);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON appointment_proposals(status);

-- M:N zwischen Terminvorschlag und Wartungsauftrag.
CREATE TABLE IF NOT EXISTS appointment_proposal_orders (
  proposal_id INTEGER NOT NULL REFERENCES appointment_proposals(id),
  order_id    INTEGER NOT NULL REFERENCES maintenance_orders(id),
  PRIMARY KEY (proposal_id, order_id)
);

CREATE INDEX IF NOT EXISTS idx_ppo_order ON appointment_proposal_orders(order_id);
