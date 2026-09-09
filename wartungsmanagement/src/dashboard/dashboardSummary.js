import { ProposalStatus } from '../constants/status.js';
import { listAllProposals } from '../models/appointmentProposals.js';

/**
 * Milestone 16 (Basis): Kennzahlen für die Dashboard-Kachel
 * "Terminvorschläge" (z. B. "12 neue Vorschläge, 7 freie Termine, ...").
 */
export function proposalSummary(db) {
  const proposals = listAllProposals(db);
  const count = (status) => proposals.filter((p) => p.status === status).length;
  return {
    neu: count(ProposalStatus.NEU),
    frei: count(ProposalStatus.FREI),
    belegt: count(ProposalStatus.BELEGT) + count(ProposalStatus.TEILWEISE_BELEGT),
    manuellePruefung: count(ProposalStatus.MANUELLE_PRUEFUNG),
    ausgewaehlt: count(ProposalStatus.AUSGEWAEHLT),
    bestaetigt: count(ProposalStatus.BESTAETIGT),
    total: proposals.length,
  };
}

/**
 * Wartungskalender-Ansichten (Milestone 16): liefert alle bestätigten
 * Termine in einem Zeitraum, wahlweise nach Hersteller/Gerät/Standort
 * gruppiert. Farbliche Kennzeichnung ist laut Vorgabe eine spätere
 * UI-Ergänzung und hier bewusst nicht Teil der Datenschicht.
 */
export function confirmedAppointmentsInRange(db, { fromDate, toDate }) {
  return listAllProposals(db).filter(
    (p) =>
      p.status === ProposalStatus.BESTAETIGT &&
      p.proposal_date >= fromDate &&
      p.proposal_date <= toDate
  );
}

export function groupAppointments(appointments, groupBy) {
  const keyFor = {
    hersteller: (p) => String(p.manufacturer_id),
    geraet: (p) => p.orders.map((o) => o.inventory_number).join(', '),
    standort: (p) => p.orders.map((o) => o.location ?? 'Unbekannt').join(', '),
  }[groupBy];
  if (!keyFor) throw new Error(`Unbekannte Gruppierung: ${groupBy}`);

  const groups = new Map();
  for (const appointment of appointments) {
    const key = keyFor(appointment);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(appointment);
  }
  return groups;
}

export function todayRange(referenceDate = new Date()) {
  const iso = referenceDate.toISOString().slice(0, 10);
  return { fromDate: iso, toDate: iso };
}

export function weekRange(referenceDate = new Date()) {
  const day = referenceDate.getDay();
  const diffToMonday = (day + 6) % 7;
  const monday = new Date(referenceDate);
  monday.setDate(referenceDate.getDate() - diffToMonday);
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  return { fromDate: monday.toISOString().slice(0, 10), toDate: sunday.toISOString().slice(0, 10) };
}

export function monthRange(referenceDate = new Date()) {
  const year = referenceDate.getFullYear();
  const month = referenceDate.getMonth();
  const first = new Date(year, month, 1);
  const last = new Date(year, month + 1, 0);
  return { fromDate: first.toISOString().slice(0, 10), toDate: last.toISOString().slice(0, 10) };
}
