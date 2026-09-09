const GERMAN_DATE_RE = /^(\d{1,2})\.(\d{1,2})\.(\d{2,4})$/;
const GERMAN_TIME_RE = /^(\d{1,2})[:.](\d{2})(?:\s*Uhr)?$/i;

/** "20.09.2026" -> "2026-09-20". Akzeptiert auch bereits-ISO-Werte. */
export function parseGermanDate(value) {
  if (value == null || value === '') return null;
  if (value instanceof Date) return value.toISOString().slice(0, 10);
  const str = String(value).trim();
  const isoMatch = /^(\d{4})-(\d{2})-(\d{2})/.exec(str);
  if (isoMatch) return `${isoMatch[1]}-${isoMatch[2]}-${isoMatch[3]}`;
  const m = GERMAN_DATE_RE.exec(str);
  if (!m) return null;
  let [, day, month, year] = m;
  if (year.length === 2) year = `20${year}`;
  return `${year.padStart(4, '0')}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
}

/** "08:00 Uhr" / "8.30" -> "08:00" */
export function parseGermanTime(value) {
  if (value == null || value === '') return null;
  const str = String(value).trim();
  const m = GERMAN_TIME_RE.exec(str);
  if (!m) return null;
  const [, hour, minute] = m;
  return `${hour.padStart(2, '0')}:${minute}`;
}

export function formatGermanDate(isoDate) {
  if (!isoDate) return '';
  const [year, month, day] = isoDate.split('-');
  return `${day}.${month}.${year}`;
}

/** "2026-09-15" -> "15.09" (ohne Jahr, für kompakte Listen von Terminvorschlägen). */
export function formatGermanDateShort(isoDate) {
  if (!isoDate) return '';
  const [, month, day] = isoDate.split('-');
  return `${day}.${month}`;
}
