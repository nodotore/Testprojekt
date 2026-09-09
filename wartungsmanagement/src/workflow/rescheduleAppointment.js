import { createAppointmentProposal, markSuperseded, getAppointmentProposal } from '../models/appointmentProposals.js';
import { confirmAppointment } from './confirmAppointment.js';

/**
 * Terminverschiebungs-Workflow ("Statt am 18.09. kommen wir am 22.09."):
 *  1. Neuen Terminvorschlag anlegen (für dieselben Aufträge wie der alte).
 *     Er durchläuft danach ganz normal die Outlook-Prüfung wie jeder andere
 *     Vorschlag (siehe outlook/availabilityCheck.js) - hier nur erzeugt.
 *  2. Der Benutzer wird über die neue Terminoption informiert (Aufrufer/UI).
 *  3. Erst nach Bestätigung durch den Benutzer wird der bestehende
 *     Outlook-Termin verschoben (aktualisiert, nicht dupliziert) - das
 *     übernimmt confirmAppointment() automatisch, da es erkennt, dass einer
 *     der betroffenen Aufträge bereits einen bestätigten Outlook-Termin hat.
 */
export function proposeReschedule(db, oldProposalId, { proposalDate, startTime = null, endTime = null }) {
  const oldProposal = getAppointmentProposal(db, oldProposalId);
  if (!oldProposal) throw new Error(`Terminvorschlag ${oldProposalId} nicht gefunden.`);

  const newProposal = createAppointmentProposal(db, {
    manufacturerId: oldProposal.manufacturer_id,
    orderIds: oldProposal.orders.map((o) => o.id),
    proposalDate,
    startTime,
    endTime,
    proposedDurationMinutes: oldProposal.proposed_duration_minutes,
    durationSource: oldProposal.duration_source,
    sourceEmailId: oldProposal.source_email_id,
    remark: `Verschiebung von Terminvorschlag #${oldProposalId} (${oldProposal.proposal_date}).`,
  });

  return { oldProposal, newProposal };
}

/** Nach Benutzerbestätigung: neuen Termin bestätigen und alten als verschoben markieren. */
export async function confirmReschedule(db, calendarClient, { oldProposalId, newProposalId }, details = {}) {
  const confirmed = await confirmAppointment(db, calendarClient, newProposalId, details);
  markSuperseded(db, oldProposalId, newProposalId);
  return confirmed;
}
