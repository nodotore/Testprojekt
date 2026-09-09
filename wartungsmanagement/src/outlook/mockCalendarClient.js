import { randomUUID } from 'node:crypto';

/**
 * In-Memory-Implementierung des CalendarClient-Interfaces für lokale
 * Entwicklung, Tests und Demos ohne Azure-AD-Zugangsdaten. Verhält sich
 * ansonsten wie die echte Graph-Anbindung (siehe calendarClient.js).
 */
export class MockCalendarClient {
  constructor() {
    /** @type {Map<string, import('./calendarClient.js').CalendarEvent>} */
    this.events = new Map();
    /** Vorab definierte "belegt"-Blöcke, unabhängig von erzeugten Events. */
    this.busyBlocks = [];
  }

  /** Für Tests: einen externen Kalenderblock (z. B. anderer Termin) simulieren. */
  addBusyBlock(start, end, subject = 'Belegt') {
    this.busyBlocks.push({ start, end, subject });
  }

  async getFreeBusy(start, end) {
    const conflicts = [];
    for (const block of [...this.busyBlocks, ...this.events.values()]) {
      if (overlaps(start, end, block.start, block.end)) {
        conflicts.push({ start: block.start, end: block.end, subject: block.subject });
      }
    }
    if (conflicts.length === 0) return { status: 'FREI', conflicts: [] };
    const fullyCovered = conflicts.some((c) => c.start <= start && c.end >= end);
    return { status: fullyCovered ? 'BELEGT' : 'TEILWEISE_BELEGT', conflicts };
  }

  async createEvent({ subject, start, end, location, body }) {
    const id = randomUUID();
    const event = { id, subject, start, end, location, body };
    this.events.set(id, event);
    return event;
  }

  async updateEvent(eventId, updates) {
    const existing = this.events.get(eventId);
    if (!existing) throw new Error(`Kein Outlook-Termin mit ID ${eventId} gefunden (Mock).`);
    const updated = { ...existing, ...updates };
    this.events.set(eventId, updated);
    return updated;
  }

  async markEventCancelled(eventId, note = 'Absage durch Hersteller erhalten') {
    const existing = this.events.get(eventId);
    if (!existing) throw new Error(`Kein Outlook-Termin mit ID ${eventId} gefunden (Mock).`);
    const updated = { ...existing, subject: `[ABGESAGT] ${existing.subject}`, body: `${existing.body ?? ''}\n\n${note}` };
    this.events.set(eventId, updated);
    return updated;
  }

  async deleteEvent(eventId) {
    this.events.delete(eventId);
  }

  async getEvent(eventId) {
    return this.events.get(eventId) ?? null;
  }
}

function overlaps(startA, endA, startB, endB) {
  return startA < endB && startB < endA;
}
