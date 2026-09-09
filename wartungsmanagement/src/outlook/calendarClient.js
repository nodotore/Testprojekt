/**
 * Gemeinsame Schnittstelle für den Zugriff auf einen Outlook-Kalender.
 * Zwei Implementierungen:
 *  - GraphCalendarClient: echte Microsoft-Graph-API-Anbindung (Produktivbetrieb)
 *  - MockCalendarClient: In-Memory-Implementierung für Entwicklung/Tests ohne
 *    Azure-AD-Zugangsdaten
 *
 * @typedef {Object} FreeBusyResult
 * @property {'FREI'|'BELEGT'|'TEILWEISE_BELEGT'} status
 * @property {{start:string,end:string,subject?:string}[]} conflicts
 *
 * @typedef {Object} CalendarEvent
 * @property {string} id
 * @property {string} subject
 * @property {string} start ISO 8601
 * @property {string} end ISO 8601
 * @property {string} [location]
 * @property {string} [body]
 */

/**
 * Wählt anhand der Umgebungsvariablen die passende Implementierung:
 * sind AZURE-Zugangsdaten gesetzt, wird die echte Graph-API verwendet,
 * sonst der In-Memory-Mock (z. B. lokale Entwicklung, Tests, Demo).
 * @returns {Promise<import('./mockCalendarClient.js').MockCalendarClient>}
 */
export async function createCalendarClient(env = process.env) {
  const hasGraphCredentials =
    env.AZURE_TENANT_ID && env.AZURE_CLIENT_ID && env.AZURE_CLIENT_SECRET;
  if (hasGraphCredentials) {
    const { GraphCalendarClient } = await import('./graphCalendarClient.js');
    return new GraphCalendarClient({
      tenantId: env.AZURE_TENANT_ID,
      clientId: env.AZURE_CLIENT_ID,
      clientSecret: env.AZURE_CLIENT_SECRET,
      calendarUserEmail: env.OUTLOOK_CALENDAR_USER,
    });
  }
  const { MockCalendarClient } = await import('./mockCalendarClient.js');
  return new MockCalendarClient();
}
