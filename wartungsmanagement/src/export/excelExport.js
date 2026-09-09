import ExcelJS from 'exceljs';
import { listAllOrdersWithDevice } from '../models/maintenanceOrders.js';
import { listProposalsForOrder } from '../models/appointmentProposals.js';
import { ProposalStatus } from '../constants/status.js';
import { PROPOSAL_STATUS_LABELS_DE, OUTLOOK_STATUS_LABELS_DE } from '../constants/labels.js';
import { formatGermanDate, formatGermanDateShort } from '../util/germanDates.js';

const HEADERS = [
  'Hersteller',
  'Gerät',
  'Inventarnummer',
  'Terminvorschläge',
  'gewählter Termin',
  'Outlook geprüft',
  'Outlook-Status',
  'Status',
];

/**
 * Milestone 13 (erweitert): Excel-Terminübersicht je Wartungsauftrag/Gerät,
 * inkl. aller Terminvorschläge, gewähltem Termin und Outlook-Prüfergebnis.
 * @param {import('node:sqlite').DatabaseSync} db
 * @param {string} filePath
 */
export async function exportAppointmentOverview(db, filePath) {
  const workbook = new ExcelJS.Workbook();
  const sheet = workbook.addWorksheet('Terminübersicht');
  sheet.addRow(HEADERS);
  sheet.getRow(1).font = { bold: true };

  for (const row of buildRows(db)) {
    sheet.addRow(row);
  }
  sheet.columns.forEach((column) => {
    column.width = 22;
  });

  await workbook.xlsx.writeFile(filePath);
  return filePath;
}

export function buildRows(db) {
  const orders = listAllOrdersWithDevice(db);
  return orders.map((order) => {
    const proposals = listProposalsForOrder(db, order.id);
    const chosen =
      proposals.find((p) => p.status === ProposalStatus.BESTAETIGT) ??
      proposals.find((p) => p.status === ProposalStatus.AUSGEWAEHLT) ??
      null;
    const anyChecked = proposals.some((p) => p.outlook_status !== 'UNGEPRUEFT');

    return [
      order.manufacturer_name,
      `${order.device_type}${order.model ? ' ' + order.model : ''}`,
      order.inventory_number,
      proposals.map((p) => formatGermanDateShort(p.proposal_date)).join(' / '),
      chosen ? `${formatGermanDate(chosen.proposal_date)}${chosen.start_time ? ' ' + chosen.start_time : ''}` : '',
      anyChecked ? 'Ja' : 'Nein',
      chosen ? OUTLOOK_STATUS_LABELS_DE[chosen.outlook_status] ?? chosen.outlook_status : '',
      chosen
        ? PROPOSAL_STATUS_LABELS_DE[chosen.status] ?? chosen.status
        : PROPOSAL_STATUS_LABELS_DE[proposals[0]?.status] ?? '',
    ];
  });
}
