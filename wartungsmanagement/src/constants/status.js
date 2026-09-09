// Terminstatus je Terminvorschlag (appointment_proposals.status)
export const ProposalStatus = Object.freeze({
  NEU: 'NEU',
  OUTLOOK_PRUEFUNG_OFFEN: 'OUTLOOK_PRUEFUNG_OFFEN',
  FREI: 'FREI',
  BELEGT: 'BELEGT',
  TEILWEISE_BELEGT: 'TEILWEISE_BELEGT',
  MANUELLE_PRUEFUNG: 'MANUELLE_PRUEFUNG',
  AUSGEWAEHLT: 'AUSGEWAEHLT',
  ABGELEHNT: 'ABGELEHNT',
  BESTAETIGT: 'BESTAETIGT',
  ABSAGE_ERHALTEN: 'ABSAGE_ERHALTEN',
  VERSCHOBEN: 'VERSCHOBEN',
});

// Rohergebnis der Outlook-Verfügbarkeitsprüfung (appointment_proposals.outlook_status)
export const OutlookAvailability = Object.freeze({
  UNGEPRUEFT: 'UNGEPRUEFT',
  FREI: 'FREI',
  BELEGT: 'BELEGT',
  TEILWEISE_BELEGT: 'TEILWEISE_BELEGT',
  AUSSERHALB_ARBEITSZEIT: 'AUSSERHALB_ARBEITSZEIT',
  KOLLISION_INTERNE_WARTUNG: 'KOLLISION_INTERNE_WARTUNG',
});

// Status eines einzelnen Wartungsauftrags (maintenance_orders.status)
export const OrderStatus = Object.freeze({
  OFFEN: 'OFFEN',
  ANFRAGE_VERSENDET: 'ANFRAGE_VERSENDET',
  TERMIN_VORGESCHLAGEN: 'TERMIN_VORGESCHLAGEN',
  TERMIN_BESTAETIGT: 'TERMIN_BESTAETIGT',
  ABGESCHLOSSEN: 'ABGESCHLOSSEN',
  ABGESAGT: 'ABGESAGT',
});
