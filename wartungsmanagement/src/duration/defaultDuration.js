export const UNKNOWN_DURATION_MESSAGE = 'Dauer unbekannt – manuelle Eingabe erforderlich';

/**
 * Ermittelt die Dauer für ein einzelnes Gerät:
 * 1. gerätespezifisch gespeicherte Standarddauer
 * 2. Standarddauer des Gerätetyps
 * 3. unbekannt
 */
export function resolveDeviceDuration(db, device) {
  if (device.default_duration_minutes != null) {
    return { minutes: device.default_duration_minutes, source: 'GERAET' };
  }
  const typeDefault = db
    .prepare('SELECT default_duration_minutes FROM device_type_defaults WHERE device_type = ?')
    .get(device.device_type);
  if (typeDefault) {
    return { minutes: typeDefault.default_duration_minutes, source: 'GERAETETYP' };
  }
  return { minutes: null, source: null };
}

/**
 * Ermittelt die Dauer für einen Terminvorschlag, der ein oder mehrere Geräte
 * betrifft. Nennt der Hersteller selbst eine Dauer im Text, hat diese
 * Vorrang. Andernfalls werden die (Standard-)Dauern der beteiligten Geräte
 * aufsummiert (mehrere Geräte am selben Termin = mehr Gesamtzeit). Fehlt für
 * mindestens ein Gerät jede Angabe, gilt die Dauer insgesamt als unbekannt -
 * es darf keine Dauer geraten werden.
 *
 * @param {import('node:sqlite').DatabaseSync} db
 * @param {{explicitMinutes?: number|null, devices: object[]}} params
 */
export function resolveProposalDuration(db, { explicitMinutes = null, devices }) {
  if (explicitMinutes != null) {
    return { minutes: explicitMinutes, source: 'HERSTELLER_ANGABE', message: null };
  }
  if (!devices || devices.length === 0) {
    return { minutes: null, source: null, message: UNKNOWN_DURATION_MESSAGE };
  }

  let total = 0;
  const sources = new Set();
  for (const device of devices) {
    const { minutes, source } = resolveDeviceDuration(db, device);
    if (minutes == null) {
      return { minutes: null, source: null, message: UNKNOWN_DURATION_MESSAGE };
    }
    total += minutes;
    sources.add(source);
  }
  const source = sources.size === 1 ? [...sources][0] : 'STANDARDDAUER_GEMISCHT';
  return { minutes: total, source, message: null };
}
