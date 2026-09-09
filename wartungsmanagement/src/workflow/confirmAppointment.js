import { ProposalStatus, OrderStatus } from '../constants/status.js';
import {
  getAppointmentProposal,
  updateProposalStatus,
  setProposalOutlookEvent,
  listConfirmedProposalsOverlapping,
} from '../models/appointmentProposals.js';
import { setOrderStatus } from '../models/maintenanceOrders.js';
import { resolveProposalDuration } from '../duration/defaultDuration.js';
import { getManufacturer } from '../models/manufacturers.js';

/**
 * Workflow (siehe Lastenheft):
 *   Herstellerantwort -> Termine erkennen -> Outlook prüfen -> freie Termine
 *   anzeigen -> Benutzer wählt Termin -> Termin bestätigen -> Outlook-Eintrag
 *   erstellen.
 * Der Outlook-Eintrag wird also bewusst erst hier, NACH der Bestätigung
 * durch den Benutzer, angelegt - nie automatisch bei der reinen
 * Verfügbarkeitsprüfung.
 */

/** Benutzer wählt einen von mehreren geprüften Terminvorschlägen aus. */
export function selectProposal(db, proposalId) {
  return updateProposalStatus(db, proposalId, ProposalStatus.AUSGEWAEHLT);
}

/** Benutzer lehnt einen Terminvorschlag ab (z. B. zugunsten eines anderen). */
export function rejectProposal(db, proposalId) {
  return updateProposalStatus(db, proposalId, ProposalStatus.ABGELEHNT);
}

/**
 * Bestätigt einen ausgewählten Terminvorschlag endgültig:
 *  - legt einen Outlook-Termin an, der alle beteiligten Geräte/Aufträge
 *    gemeinsam nennt, ODER aktualisiert einen bereits bestehenden
 *    Outlook-Termin, falls einer der beteiligten Aufträge schon einen
 *    bestätigten Termin hatte (= Terminverschiebung, siehe unten)
 *  - setzt die betroffenen Wartungsaufträge auf TERMIN_BESTAETIGT
 *  - lehnt konkurrierende Terminvorschläge für dieselben Aufträge automatisch ab
 *
 * @param {import('node:sqlite').DatabaseSync} db
 * @param {import('../outlook/mockCalendarClient.js').MockCalendarClient} calendarClient
 * @param {number} proposalId
 * @param {{technician?: string, location?: string}} [details]
 */
export async function confirmAppointment(db, calendarClient, proposalId, details = {}) {
  const proposal = getAppointmentProposal(db, proposalId);
  if (!proposal) throw new Error(`Terminvorschlag ${proposalId} nicht gefunden.`);

  const duration =
    proposal.proposed_duration_minutes ??
    resolveProposalDuration(db, { devices: proposal.orders }).minutes;
  if (!proposal.start_time || duration == null) {
    throw new Error(
      'Termin kann nicht bestätigt werden: Uhrzeit und/oder Dauer fehlen (manuelle Eingabe erforderlich).'
    );
  }

  const start = new Date(`${proposal.proposal_date}T${proposal.start_time}:00`);
  const end = proposal.end_time
    ? new Date(`${proposal.proposal_date}T${proposal.end_time}:00`)
    : new Date(start.getTime() + duration * 60_000);

  const manufacturer = getManufacturer(db, proposal.manufacturer_id);
  const eventPayload = buildEventPayload(proposal, manufacturer, start, end, details);

  const existingEventId = findExistingConfirmedEventId(db, proposal);
  let event;
  if (existingEventId) {
    event = await calendarClient.updateEvent(existingEventId, eventPayload);
  } else {
    event = await calendarClient.createEvent(eventPayload);
  }

  setProposalOutlookEvent(db, proposalId, {
    eventId: event.id,
    start: eventPayload.start,
    end: eventPayload.end,
  });
  updateProposalStatus(db, proposalId, ProposalStatus.BESTAETIGT);

  for (const order of proposal.orders) {
    setOrderStatus(db, order.id, OrderStatus.TERMIN_BESTAETIGT);
  }

  rejectCompetingProposals(db, proposal);

  return getAppointmentProposal(db, proposalId);
}

function buildEventPayload(proposal, manufacturer, start, end, details) {
  const deviceLines = proposal.orders
    .map((o) => `- ${o.device_type}${o.model ? ' ' + o.model : ''} – ${o.inventory_number}`)
    .join('\n');
  const orderLines = proposal.orders.map((o) => `- ${o.order_number}`).join('\n');
  const subject = `Wartung – ${manufacturer.name} – ${proposal.orders.length} Gerät${proposal.orders.length === 1 ? '' : 'e'}`;
  const body = [
    `Hersteller: ${manufacturer.name}`,
    details.technician ? `Techniker: ${details.technician}` : null,
    '',
    'Geräte:',
    deviceLines,
    '',
    'Wartungsaufträge:',
    orderLines,
    manufacturer.contact_email ? `\nKontakt:\n${manufacturer.contact_email}` : null,
  ]
    .filter((line) => line !== null)
    .join('\n');

  return {
    subject,
    start: start.toISOString(),
    end: end.toISOString(),
    location: details.location ?? null,
    body,
  };
}

/**
 * Prüft, ob einer der von diesem Vorschlag betroffenen Aufträge bereits
 * einen bestätigten Outlook-Termin hat (= dies ist eine Verschiebung, kein
 * neuer Termin). Es darf nie ein zweiter Outlook-Termin für denselben
 * Auftrag entstehen.
 */
function findExistingConfirmedEventId(db, proposal) {
  const orderIds = new Set(proposal.orders.map((o) => o.id));
  const confirmed = listConfirmedProposalsOverlapping(db, { excludeProposalId: proposal.id });
  for (const other of confirmed) {
    if (!other.outlook_event_id) continue;
    if (other.orders.some((o) => orderIds.has(o.id))) return other.outlook_event_id;
  }
  return null;
}

function rejectCompetingProposals(db, confirmedProposal) {
  const orderIds = confirmedProposal.orders.map((o) => o.id);
  if (orderIds.length === 0) return;
  const placeholders = orderIds.map(() => '?').join(',');
  const competing = db
    .prepare(
      `SELECT DISTINCT ap.id FROM appointment_proposals ap
       JOIN appointment_proposal_orders ppo ON ppo.proposal_id = ap.id
       WHERE ppo.order_id IN (${placeholders}) AND ap.id != ?
         AND ap.status NOT IN (?, ?)`
    )
    .all(...orderIds, confirmedProposal.id, ProposalStatus.ABGELEHNT, ProposalStatus.BESTAETIGT);
  for (const row of competing) {
    updateProposalStatus(db, row.id, ProposalStatus.ABGELEHNT);
  }
}
