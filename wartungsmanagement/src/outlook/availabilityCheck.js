import { ProposalStatus, OutlookAvailability } from '../constants/status.js';
import { resolveProposalDuration, UNKNOWN_DURATION_MESSAGE } from '../duration/defaultDuration.js';
import { updateProposalOutlookCheck } from '../models/appointmentProposals.js';

const DEFAULT_WORKING_HOURS = { startHour: 8, endHour: 17 };
const DEFAULT_WORKING_WEEKDAYS = [1, 2, 3, 4, 5]; // Mo-Fr (0=So)

/**
 * Milestone 9: Prüft einen einzelnen Terminvorschlag gegen den Outlook-
 * Kalender und die weiteren im Lastenheft genannten Kriterien (Zeitraum
 * frei? Überschneidung? außerhalb Arbeitszeit? Kollision mit anderer
 * Wartung?).
 *
 * Ein bestätigter Wartungstermin wird laut Workflow erst NACH Bestätigung
 * als eigener Outlook-Termin angelegt (siehe workflow/confirmAppointment.js).
 * Dadurch deckt die Outlook-Verfügbarkeitsprüfung automatisch auch
 * "Kollision mit einem anderen bereits bestätigten Wartungstermin" mit ab -
 * eine separate interne Kollisionsprüfung wäre nur eine Duplizierung
 * derselben Information und wird deshalb bewusst nicht zusätzlich geführt.
 *
 * @param {import('node:sqlite').DatabaseSync} db
 * @param {import('./mockCalendarClient.js').MockCalendarClient} calendarClient
 * @param {object} proposal Terminvorschlag inkl. `.orders` (siehe getAppointmentProposal)
 * @param {{workingHours?:{startHour:number,endHour:number}, workingWeekdays?:number[]}} [options]
 */
export async function checkProposalAvailability(db, calendarClient, proposal, options = {}) {
  const workingHours = options.workingHours ?? DEFAULT_WORKING_HOURS;
  const workingWeekdays = options.workingWeekdays ?? DEFAULT_WORKING_WEEKDAYS;

  if (!proposal.start_time) {
    return updateProposalOutlookCheck(db, proposal.id, {
      outlookStatus: OutlookAvailability.UNGEPRUEFT,
      status: ProposalStatus.MANUELLE_PRUEFUNG,
      remark: 'Keine Uhrzeit angegeben – manuelle Prüfung erforderlich.',
    });
  }

  const duration =
    proposal.proposed_duration_minutes ??
    resolveProposalDuration(db, { devices: proposal.orders }).minutes;
  if (duration == null) {
    return updateProposalOutlookCheck(db, proposal.id, {
      outlookStatus: OutlookAvailability.UNGEPRUEFT,
      status: ProposalStatus.MANUELLE_PRUEFUNG,
      remark: UNKNOWN_DURATION_MESSAGE,
    });
  }

  const start = new Date(`${proposal.proposal_date}T${proposal.start_time}:00`);
  const end = proposal.end_time
    ? new Date(`${proposal.proposal_date}T${proposal.end_time}:00`)
    : new Date(start.getTime() + duration * 60_000);

  if (!isWithinWorkingHours(start, end, workingHours, workingWeekdays)) {
    return updateProposalOutlookCheck(db, proposal.id, {
      outlookStatus: OutlookAvailability.AUSSERHALB_ARBEITSZEIT,
      status: ProposalStatus.MANUELLE_PRUEFUNG,
      remark: 'Zeitraum liegt außerhalb der Arbeitszeit – manuelle Prüfung erforderlich.',
    });
  }

  const freeBusy = await calendarClient.getFreeBusy(start.toISOString(), end.toISOString());
  const status =
    freeBusy.status === 'FREI'
      ? ProposalStatus.FREI
      : freeBusy.status === 'TEILWEISE_BELEGT'
        ? ProposalStatus.TEILWEISE_BELEGT
        : ProposalStatus.BELEGT;

  return updateProposalOutlookCheck(db, proposal.id, {
    outlookStatus: freeBusy.status,
    status,
    remark:
      freeBusy.conflicts.length > 0
        ? `Kollidiert mit: ${freeBusy.conflicts.map((c) => c.subject).join(', ')}`
        : null,
  });
}

export async function checkAllProposals(db, calendarClient, proposals, options = {}) {
  const results = [];
  for (const proposal of proposals) {
    results.push(await checkProposalAvailability(db, calendarClient, proposal, options));
  }
  return results;
}

// proposal_date/start_time werden bewusst ohne Zeitzonen-Suffix geparst, also
// als lokale Wanduhrzeit vor Ort interpretiert - genau das braucht die
// Arbeitszeitprüfung. Für den Graph-Aufruf wird daraus über toISOString()
// trotzdem ein eindeutiger Zeitpunkt.
function isWithinWorkingHours(start, end, { startHour, endHour }, workingWeekdays) {
  if (!workingWeekdays.includes(start.getDay())) return false;
  const startMinutes = start.getHours() * 60 + start.getMinutes();
  const endMinutes = end.getHours() * 60 + end.getMinutes();
  return startMinutes >= startHour * 60 && endMinutes <= endHour * 60 && end.getDate() === start.getDate();
}
