import test from 'node:test';
import assert from 'node:assert/strict';
import { setupDb } from './helpers.js';
import { resolveProposalDuration, UNKNOWN_DURATION_MESSAGE } from '../src/duration/defaultDuration.js';

test('Standarddauer je Gerätetyp', () => {
  const db = setupDb();
  assert.equal(
    resolveProposalDuration(db, { devices: [{ device_type: 'Dialysegerät', default_duration_minutes: null }] })
      .minutes,
    120
  );
  assert.equal(
    resolveProposalDuration(db, { devices: [{ device_type: 'Patientenmonitor', default_duration_minutes: null }] })
      .minutes,
    60
  );
  assert.equal(
    resolveProposalDuration(db, { devices: [{ device_type: 'Defibrillator', default_duration_minutes: null }] })
      .minutes,
    90
  );
});

test('gerätespezifische Dauer hat Vorrang vor Gerätetyp-Standard', () => {
  const db = setupDb();
  const result = resolveProposalDuration(db, {
    devices: [{ device_type: 'Dialysegerät', default_duration_minutes: 45 }],
  });
  assert.equal(result.minutes, 45);
  assert.equal(result.source, 'GERAET');
});

test('explizite Angabe des Herstellers hat Vorrang vor jeder Standarddauer', () => {
  const db = setupDb();
  const result = resolveProposalDuration(db, {
    explicitMinutes: 200,
    devices: [{ device_type: 'Dialysegerät', default_duration_minutes: 45 }],
  });
  assert.equal(result.minutes, 200);
  assert.equal(result.source, 'HERSTELLER_ANGABE');
});

test('unbekannter Gerätetyp ohne eigene Dauer -> manuelle Eingabe erforderlich, keine geratene Dauer', () => {
  const db = setupDb();
  const result = resolveProposalDuration(db, {
    devices: [{ device_type: 'Ultraschallgerät', default_duration_minutes: null }],
  });
  assert.equal(result.minutes, null);
  assert.equal(result.message, UNKNOWN_DURATION_MESSAGE);
});

test('mehrere Geräte an einem Termin: Dauern werden aufsummiert', () => {
  const db = setupDb();
  const result = resolveProposalDuration(db, {
    devices: [
      { device_type: 'Dialysegerät', default_duration_minutes: null },
      { device_type: 'Patientenmonitor', default_duration_minutes: null },
    ],
  });
  assert.equal(result.minutes, 180);
});
