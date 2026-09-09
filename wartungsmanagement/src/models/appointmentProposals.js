import { ProposalStatus, OutlookAvailability } from '../constants/status.js';
import { nowIso } from '../db/db.js';

/**
 * Legt einen Terminvorschlag an und verknüpft ihn mit einem oder mehreren
 * Wartungsaufträgen (M:N). Ein Terminvorschlag kann sich auf ein einzelnes
 * Gerät oder auf mehrere gleichzeitig beziehen.
 */
export function createAppointmentProposal(
  db,
  { manufacturerId, orderIds, proposalDate, startTime = null, endTime = null, proposedDurationMinutes = null, durationSource = null, sourceEmailId = null, remark = null }
) {
  if (!orderIds || orderIds.length === 0) {
    throw new Error('Ein Terminvorschlag benötigt mindestens einen Wartungsauftrag.');
  }
  const { lastInsertRowid } = db
    .prepare(
      `INSERT INTO appointment_proposals
         (manufacturer_id, proposal_date, start_time, end_time, proposed_duration_minutes,
          duration_source, source_email_id, outlook_status, status, remark)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
    .run(
      manufacturerId,
      proposalDate,
      startTime,
      endTime,
      proposedDurationMinutes,
      durationSource,
      sourceEmailId,
      OutlookAvailability.UNGEPRUEFT,
      ProposalStatus.NEU,
      remark
    );
  const link = db.prepare(
    'INSERT INTO appointment_proposal_orders (proposal_id, order_id) VALUES (?, ?)'
  );
  for (const orderId of orderIds) link.run(lastInsertRowid, orderId);
  return getAppointmentProposal(db, lastInsertRowid);
}

export function getAppointmentProposal(db, id) {
  const proposal = db.prepare('SELECT * FROM appointment_proposals WHERE id = ?').get(id);
  if (!proposal) return null;
  return { ...proposal, orders: getOrdersForProposal(db, id) };
}

export function getOrdersForProposal(db, proposalId) {
  return db
    .prepare(
      `SELECT mo.*, d.device_type, d.model, d.inventory_number, d.serial_number,
              d.default_duration_minutes, d.location
       FROM appointment_proposal_orders ppo
       JOIN maintenance_orders mo ON mo.id = ppo.order_id
       JOIN devices d ON d.id = mo.device_id
       WHERE ppo.proposal_id = ?
       ORDER BY d.device_type, d.inventory_number`
    )
    .all(proposalId);
}

export function listProposalsForOrder(db, orderId) {
  return db
    .prepare(
      `SELECT ap.* FROM appointment_proposals ap
       JOIN appointment_proposal_orders ppo ON ppo.proposal_id = ap.id
       WHERE ppo.order_id = ?
       ORDER BY ap.proposal_date, ap.start_time`
    )
    .all(orderId)
    .map((p) => ({ ...p, orders: getOrdersForProposal(db, p.id) }));
}

export function listProposalsByManufacturer(db, manufacturerId) {
  return db
    .prepare('SELECT * FROM appointment_proposals WHERE manufacturer_id = ? ORDER BY proposal_date, start_time')
    .all(manufacturerId)
    .map((p) => ({ ...p, orders: getOrdersForProposal(db, p.id) }));
}

export function listAllProposals(db) {
  return db
    .prepare('SELECT * FROM appointment_proposals ORDER BY proposal_date, start_time')
    .all()
    .map((p) => ({ ...p, orders: getOrdersForProposal(db, p.id) }));
}

export function updateProposalStatus(db, proposalId, status) {
  db.prepare('UPDATE appointment_proposals SET status = ?, updated_at = ? WHERE id = ?').run(
    status,
    nowIso(),
    proposalId
  );
  return getAppointmentProposal(db, proposalId);
}

export function updateProposalOutlookCheck(db, proposalId, { outlookStatus, status, remark = null }) {
  db.prepare(
    `UPDATE appointment_proposals
     SET outlook_status = ?, status = ?, remark = COALESCE(?, remark), updated_at = ?
     WHERE id = ?`
  ).run(outlookStatus, status, remark, nowIso(), proposalId);
  return getAppointmentProposal(db, proposalId);
}

export function setProposalOutlookEvent(db, proposalId, { eventId, start, end }) {
  db.prepare(
    `UPDATE appointment_proposals
     SET outlook_event_id = ?, outlook_event_start = ?, outlook_event_end = ?, updated_at = ?
     WHERE id = ?`
  ).run(eventId, start, end, nowIso(), proposalId);
  return getAppointmentProposal(db, proposalId);
}

export function markSuperseded(db, proposalId, supersededByProposalId) {
  db.prepare(
    `UPDATE appointment_proposals
     SET status = ?, superseded_by_proposal_id = ?, updated_at = ?
     WHERE id = ?`
  ).run(ProposalStatus.VERSCHOBEN, supersededByProposalId, nowIso(), proposalId);
}

/** Alle bestätigten Terminvorschläge, die einen Wartungsauftrag betreffen (für Kollisionsprüfung). */
export function listConfirmedProposalsOverlapping(db, { excludeProposalId = null } = {}) {
  const rows = db
    .prepare(
      `SELECT * FROM appointment_proposals
       WHERE status = ? AND (? IS NULL OR id != ?)`
    )
    .all(ProposalStatus.BESTAETIGT, excludeProposalId, excludeProposalId);
  return rows.map((p) => ({ ...p, orders: getOrdersForProposal(db, p.id) }));
}
