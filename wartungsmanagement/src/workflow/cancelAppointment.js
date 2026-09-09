import { ProposalStatus, OrderStatus } from '../constants/status.js';
import { getAppointmentProposal, updateProposalStatus } from '../models/appointmentProposals.js';
import { setOrderStatus } from '../models/maintenanceOrders.js';

/**
 * Absage-Workflow (siehe Lastenheft, Abschnitt "Absagen"):
 *  1. Nachricht wurde bereits erkannt (Aufrufer identifiziert den Vorschlag).
 *  2/3. Status auf ABSAGE_ERHALTEN setzen.
 *  4. Outlook-Termin markieren (nicht löschen!).
 *  5. Ergebnis enthält eine Rückfrage an den Benutzer ("Kalendertermin
 *     löschen?") - das Löschen erfolgt niemals automatisch, sondern nur über
 *     den separaten Aufruf von deleteOutlookEvent() nach Benutzerbestätigung.
 *
 * Die betroffenen Wartungsaufträge gehen zurück auf OFFEN, da das Gerät
 * weiterhin gewartet werden muss - nur der konkrete Termin ist entfallen.
 */
export async function cancelAppointment(db, calendarClient, proposalId, { note } = {}) {
  const proposal = getAppointmentProposal(db, proposalId);
  if (!proposal) throw new Error(`Terminvorschlag ${proposalId} nicht gefunden.`);

  updateProposalStatus(db, proposalId, ProposalStatus.ABSAGE_ERHALTEN);
  for (const order of proposal.orders) {
    setOrderStatus(db, order.id, OrderStatus.OFFEN);
  }

  let markedOutlookEvent = null;
  if (proposal.outlook_event_id) {
    markedOutlookEvent = await calendarClient.markEventCancelled(
      proposal.outlook_event_id,
      note ?? 'Absage durch Hersteller erhalten'
    );
  }

  return {
    proposal: getAppointmentProposal(db, proposalId),
    markedOutlookEvent,
    requiresUserDecision: Boolean(proposal.outlook_event_id),
    userPrompt: proposal.outlook_event_id ? 'Kalendertermin löschen?' : null,
  };
}

/**
 * Löscht den Outlook-Termin einer abgesagten Wartung endgültig. Darf laut
 * Vorgabe nur nach expliziter Bestätigung durch den Benutzer aufgerufen
 * werden (siehe userPrompt aus cancelAppointment()).
 */
export async function deleteOutlookEvent(db, calendarClient, proposalId) {
  const proposal = getAppointmentProposal(db, proposalId);
  if (!proposal?.outlook_event_id) return;
  await calendarClient.deleteEvent(proposal.outlook_event_id);
  db.prepare(
    `UPDATE appointment_proposals
     SET outlook_event_id = NULL, outlook_event_start = NULL, outlook_event_end = NULL
     WHERE id = ?`
  ).run(proposalId);
}
