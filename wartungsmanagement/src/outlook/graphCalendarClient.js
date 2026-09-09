import { Client } from '@microsoft/microsoft-graph-client';
import { ClientSecretCredential } from '@azure/identity';
import 'isomorphic-fetch';

const GRAPH_SCOPE = 'https://graph.microsoft.com/.default';

/**
 * Echte Microsoft-Graph-API-Anbindung an einen Outlook-Kalender (App-Only /
 * Client-Credentials-Flow). Benötigt eine Azure-AD-App-Registrierung mit den
 * Anwendungsberechtigungen "Calendars.ReadWrite" (Admin-Consent erforderlich)
 * sowie die Umgebungsvariablen AZURE_TENANT_ID, AZURE_CLIENT_ID,
 * AZURE_CLIENT_SECRET und OUTLOOK_CALENDAR_USER (Postfach/Kalender, gegen den
 * geprüft und in den Termine angelegt werden).
 */
export class GraphCalendarClient {
  constructor({ tenantId, clientId, clientSecret, calendarUserEmail }) {
    if (!calendarUserEmail) {
      throw new Error('OUTLOOK_CALENDAR_USER (Ziel-Kalender) ist nicht gesetzt.');
    }
    const credential = new ClientSecretCredential(tenantId, clientId, clientSecret);
    this.calendarUserEmail = calendarUserEmail;
    this.client = Client.initWithMiddleware({
      authProvider: {
        getAccessToken: async () => {
          const token = await credential.getToken(GRAPH_SCOPE);
          return token.token;
        },
      },
    });
  }

  /**
   * Fragt die Verfügbarkeit über /getSchedule ab (liefert direkt
   * frei/belegt/teilweise ohne Zugriff auf fremde Terminkalender-Details).
   */
  async getFreeBusy(start, end) {
    const response = await this.client
      .api(`/users/${this.calendarUserEmail}/calendar/getSchedule`)
      .post({
        schedules: [this.calendarUserEmail],
        startTime: { dateTime: start, timeZone: 'UTC' },
        endTime: { dateTime: end, timeZone: 'UTC' },
        availabilityViewInterval: 30,
      });

    const schedule = response.value?.[0];
    const items = schedule?.scheduleItems ?? [];
    const conflicts = items
      .filter((item) => item.status && item.status !== 'free')
      .map((item) => ({
        start: item.start?.dateTime,
        end: item.end?.dateTime,
        subject: item.subject ?? 'Belegt',
      }));

    if (conflicts.length === 0) return { status: 'FREI', conflicts: [] };
    const fullyCovered = conflicts.some((c) => c.start <= start && c.end >= end);
    return { status: fullyCovered ? 'BELEGT' : 'TEILWEISE_BELEGT', conflicts };
  }

  async createEvent({ subject, start, end, location, body }) {
    const event = await this.client
      .api(`/users/${this.calendarUserEmail}/events`)
      .post(toGraphEvent({ subject, start, end, location, body }));
    return fromGraphEvent(event);
  }

  async updateEvent(eventId, updates) {
    const event = await this.client
      .api(`/users/${this.calendarUserEmail}/events/${eventId}`)
      .patch(toGraphEvent(updates));
    return fromGraphEvent(event);
  }

  async markEventCancelled(eventId, note = 'Absage durch Hersteller erhalten') {
    const existing = await this.getEvent(eventId);
    return this.updateEvent(eventId, {
      subject: `[ABGESAGT] ${existing.subject}`,
      body: `${existing.body ?? ''}\n\n${note}`,
    });
  }

  async deleteEvent(eventId) {
    await this.client.api(`/users/${this.calendarUserEmail}/events/${eventId}`).delete();
  }

  async getEvent(eventId) {
    const event = await this.client
      .api(`/users/${this.calendarUserEmail}/events/${eventId}`)
      .get();
    return fromGraphEvent(event);
  }
}

function toGraphEvent({ subject, start, end, location, body }) {
  const payload = {};
  if (subject !== undefined) payload.subject = subject;
  if (start !== undefined) payload.start = { dateTime: start, timeZone: 'UTC' };
  if (end !== undefined) payload.end = { dateTime: end, timeZone: 'UTC' };
  if (location !== undefined) payload.location = { displayName: location };
  if (body !== undefined) payload.body = { contentType: 'text', content: body };
  return payload;
}

function fromGraphEvent(event) {
  return {
    id: event.id,
    subject: event.subject,
    start: event.start?.dateTime,
    end: event.end?.dateTime,
    location: event.location?.displayName,
    body: event.body?.content,
  };
}
