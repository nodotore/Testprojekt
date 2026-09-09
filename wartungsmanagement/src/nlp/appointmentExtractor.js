/**
 * Regelbasierte Erkennung von Terminvorschlägen in Hersteller-E-Mails
 * (Milestone 7/8, erweitert um mehrere Termine, mehrere Geräte pro Termin,
 * unterschiedliche Termine pro Gerät und mehrere Alternativen pro Gerät).
 *
 * Kein echtes NLU/LLM, sondern deterministische Muster für die im Lastenheft
 * beschriebenen Formulierungen. Für abweichende Formulierungen ist ein
 * späterer Milestone ("KI-Auswertung der E-Mails", Milestone 7 der
 * ursprünglichen Reihenfolge) vorgesehen; diese Funktion liefert die
 * strukturierte Grundlage, auf die eine KI-Auswertung aufsetzen kann.
 */

// Kein Komma vor der Zeit erlauben: "15.09., 18.09. oder 22.09.2026" ist eine
// Terminliste, kein "Datum, Uhrzeit" - sonst würde "18.09" nach dem Komma als
// Uhrzeit "18:09" des vorherigen Datums fehlinterpretiert.
const DATE_TIME_CHUNK_RE =
  /(\d{1,2})\.(\d{1,2})\.(\d{2,4})?(?:\s*[-–]?\s*(?:um\s*)?(\d{1,2})[:.](\d{2})\s*(?:Uhr)?)?/g;

const DURATION_RE = /(\d+(?:[.,]\d+)?)\s*(Stunden?|Std\.?|Minuten?|Min\.?)/i;

/**
 * @param {string} text E-Mail-Freitext
 * @param {{orderId:number, inventoryNumber:string}[]} orders Wartungsaufträge im Kontext dieser E-Mail
 * @param {{defaultYear?: number}} [options]
 * @returns {{orderIds:number[], date:string, startTime:string|null, proposedDurationMinutes:number|null}[]}
 */
export function extractAppointmentProposals(text, orders, options = {}) {
  const defaultYear = options.defaultYear ?? inferDefaultYear();
  const segments = splitIntoDeviceSegments(text, orders);

  const results = [];
  for (const segment of segments) {
    const duration = extractDurationMinutes(segment.text);
    const dates = extractDates(segment.text, defaultYear);
    for (const d of dates) {
      results.push({
        orderIds: segment.orderIds,
        date: d.date,
        startTime: d.time,
        proposedDurationMinutes: duration,
      });
    }
  }
  return results;
}

function splitIntoDeviceSegments(text, orders) {
  const allOrderIds = orders.map((o) => o.orderId);
  if (!orders.length) return [{ text, orderIds: [] }];

  const markers = [];
  for (const order of orders) {
    const needle = order.inventoryNumber;
    if (!needle) continue;
    let fromIndex = 0;
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const idx = text.indexOf(needle, fromIndex);
      if (idx === -1) break;
      markers.push({ index: idx, orderId: order.orderId });
      fromIndex = idx + needle.length;
    }
  }
  markers.sort((a, b) => a.index - b.index);

  if (markers.length === 0) {
    return [{ text, orderIds: allOrderIds }];
  }

  const segments = [];
  if (markers[0].index > 0) {
    const lead = text.slice(0, markers[0].index);
    if (DATE_TIME_CHUNK_RE.test(lead)) {
      segments.push({ text: lead, orderIds: allOrderIds });
    }
    DATE_TIME_CHUNK_RE.lastIndex = 0;
  }
  for (let i = 0; i < markers.length; i += 1) {
    const start = markers[i].index;
    const end = i + 1 < markers.length ? markers[i + 1].index : text.length;
    segments.push({ text: text.slice(start, end), orderIds: [markers[i].orderId] });
  }
  return segments;
}

function extractDates(text, defaultYear) {
  const matches = [...text.matchAll(DATE_TIME_CHUNK_RE)];
  const entries = matches
    .map((m) => {
      const [, day, month, year, hour, minute] = m;
      return {
        day,
        month,
        year: year ? normalizeYear(year) : null,
        time: hour ? `${hour.padStart(2, '0')}:${minute}` : null,
      };
    })
    .filter((e) => Number.parseInt(e.day, 10) <= 31 && Number.parseInt(e.month, 10) <= 12);

  // Jahr rückwärts propagieren: "15.09., 18.09. oder 22.09.2026" -> alle 2026.
  let nextYear = null;
  for (let i = entries.length - 1; i >= 0; i -= 1) {
    if (entries[i].year) {
      nextYear = entries[i].year;
    } else {
      entries[i].year = nextYear ?? defaultYear;
    }
  }

  return entries.map((e) => ({
    date: `${e.year}-${e.month.padStart(2, '0')}-${e.day.padStart(2, '0')}`,
    time: e.time,
  }));
}

function normalizeYear(year) {
  return year.length === 2 ? `20${year}` : year;
}

function extractDurationMinutes(text) {
  const m = DURATION_RE.exec(text);
  if (!m) return null;
  const value = Number.parseFloat(m[1].replace(',', '.'));
  const unit = m[2].toLowerCase();
  if (unit.startsWith('stun') || unit.startsWith('std')) return Math.round(value * 60);
  return Math.round(value);
}

function inferDefaultYear() {
  return new Date().getFullYear();
}
