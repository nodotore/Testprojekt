import { ProposalStatus } from '../constants/status.js';

/**
 * Milestone 10: Bewertet alle als FREI geprüften Terminvorschläge für eine
 * Menge von Wartungsaufträgen und schlägt vor, welcher Termin am besten
 * passt. Die endgültige Auswahl trifft weiterhin der Benutzer - diese
 * Funktion liefert nur eine priorisierte Liste.
 *
 * Priorisierung (siehe Lastenheft):
 *  1. Termin liegt vor der Wartungsfälligkeit
 *  2. Outlook-Kalender vollständig frei (Vorfilterung: nur status=FREI)
 *  3. Arbeitszeit eingehalten (ebenfalls bereits durch status=FREI erfüllt)
 *  4. Keine andere Wartung direkt daneben (siehe hasAdjacentAppointment)
 *  5+6. Mehrere Geräte desselben Herstellers an einem Termin bündeln, um die
 *     Gesamtzahl der Servicetermine zu minimieren
 *
 * @param {import('node:sqlite').DatabaseSync} db
 * @param {{orderIds:number[], proposals:object[]}} params `proposals` = alle
 *   bereits gegen Outlook geprüften Terminvorschläge, die (mindestens) einen
 *   der `orderIds` betreffen (siehe listProposalsForOrder/listProposalsByManufacturer).
 */
export function rankCandidateDates(db, { orderIds, proposals, adjacentProposals = [] }) {
  const targetOrderIds = new Set(orderIds);
  const dueDateByOrder = new Map();
  const byDate = new Map();

  for (const proposal of proposals) {
    if (proposal.status !== ProposalStatus.FREI) continue;
    const coveredHere = proposal.orders
      .map((o) => o.id)
      .filter((id) => targetOrderIds.has(id));
    if (coveredHere.length === 0) continue;
    for (const order of proposal.orders) dueDateByOrder.set(order.id, order.due_date);

    if (!byDate.has(proposal.proposal_date)) {
      byDate.set(proposal.proposal_date, {
        date: proposal.proposal_date,
        proposals: [],
        orderIds: new Set(),
      });
    }
    const bucket = byDate.get(proposal.proposal_date);
    bucket.proposals.push(proposal);
    coveredHere.forEach((id) => bucket.orderIds.add(id));
  }

  const candidates = [...byDate.values()].map((bucket) => {
    const coveredOrderIds = [...bucket.orderIds];
    const dueViolations = coveredOrderIds.filter((id) => {
      const due = dueDateByOrder.get(id);
      return due && bucket.date > due;
    }).length;
    return {
      date: bucket.date,
      proposals: bucket.proposals,
      coveredOrderIds,
      coveredCount: coveredOrderIds.length,
      dueViolations,
      hasAdjacentAppointment: hasAdjacentAppointment(bucket.proposals, adjacentProposals),
    };
  });

  candidates.sort((a, b) => {
    if (b.coveredCount !== a.coveredCount) return b.coveredCount - a.coveredCount;
    if (a.dueViolations !== b.dueViolations) return a.dueViolations - b.dueViolations;
    if (a.hasAdjacentAppointment !== b.hasAdjacentAppointment) {
      return Number(a.hasAdjacentAppointment) - Number(b.hasAdjacentAppointment);
    }
    return a.date.localeCompare(b.date);
  });

  return candidates;
}

/**
 * Greedy Set-Cover: wählt nacheinander den am besten bewerteten Termin,
 * entfernt die damit abgedeckten Geräte aus der offenen Menge und wiederholt
 * das, bis alle Geräte einen empfohlenen Termin haben oder keine freien
 * Vorschläge mehr übrig sind. Minimiert damit die Anzahl separater
 * Servicetermine.
 */
export function recommendSchedule(db, { orderIds, proposals, adjacentProposals = [] }) {
  let remaining = new Set(orderIds);
  const recommended = [];

  while (remaining.size > 0) {
    const candidates = rankCandidateDates(db, {
      orderIds: [...remaining],
      proposals,
      adjacentProposals,
    });
    if (candidates.length === 0) break;
    const best = candidates[0];
    recommended.push(best);
    for (const id of best.coveredOrderIds) remaining.delete(id);
  }

  return { recommended, uncoveredOrderIds: [...remaining] };
}

function hasAdjacentAppointment(bucketProposals, adjacentProposals) {
  if (adjacentProposals.length === 0) return false;
  return bucketProposals.some((proposal) => {
    if (!proposal.start_time) return false;
    const start = new Date(`${proposal.proposal_date}T${proposal.start_time}:00`);
    const end = proposal.end_time
      ? new Date(`${proposal.proposal_date}T${proposal.end_time}:00`)
      : null;
    return adjacentProposals.some((other) => {
      if (!other.start_time) return false;
      const otherStart = new Date(`${other.proposal_date}T${other.start_time}:00`);
      const gapMinutes = Math.abs(otherStart - (end ?? start)) / 60_000;
      return gapMinutes <= 30;
    });
  });
}
