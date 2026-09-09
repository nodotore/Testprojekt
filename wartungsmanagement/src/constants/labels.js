import { ProposalStatus, OutlookAvailability } from './status.js';

export const PROPOSAL_STATUS_LABELS_DE = {
  [ProposalStatus.NEU]: 'Neu',
  [ProposalStatus.OUTLOOK_PRUEFUNG_OFFEN]: 'Outlook-Prüfung offen',
  [ProposalStatus.FREI]: 'Frei',
  [ProposalStatus.BELEGT]: 'Belegt',
  [ProposalStatus.TEILWEISE_BELEGT]: 'Teilweise belegt',
  [ProposalStatus.MANUELLE_PRUEFUNG]: 'Manuelle Prüfung',
  [ProposalStatus.AUSGEWAEHLT]: 'Ausgewählt',
  [ProposalStatus.ABGELEHNT]: 'Abgelehnt',
  [ProposalStatus.BESTAETIGT]: 'Bestätigt',
  [ProposalStatus.ABSAGE_ERHALTEN]: 'Absage erhalten',
  [ProposalStatus.VERSCHOBEN]: 'Verschoben',
};

export const OUTLOOK_STATUS_LABELS_DE = {
  [OutlookAvailability.UNGEPRUEFT]: 'Ungeprüft',
  [OutlookAvailability.FREI]: 'Frei',
  [OutlookAvailability.BELEGT]: 'Belegt',
  [OutlookAvailability.TEILWEISE_BELEGT]: 'Teilweise belegt',
  [OutlookAvailability.AUSSERHALB_ARBEITSZEIT]: 'Außerhalb Arbeitszeit',
  [OutlookAvailability.KOLLISION_INTERNE_WARTUNG]: 'Kollision mit interner Wartung',
};
