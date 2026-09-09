import { listManufacturers } from '../models/manufacturers.js';
import { listOpenOrdersByManufacturer } from '../models/maintenanceOrders.js';
import { createMaintenanceRequest } from '../models/maintenanceRequests.js';

/**
 * Milestone 2: Gruppiert alle offenen Wartungsaufträge nach Hersteller.
 * Jedes Gerät bleibt als eigene Zeile/eigener Auftrag sichtbar.
 */
export function groupOpenOrdersByManufacturer(db) {
  return listManufacturers(db)
    .map((manufacturer) => ({
      manufacturer,
      openOrders: listOpenOrdersByManufacturer(db, manufacturer.id),
    }))
    .filter((group) => group.openOrders.length > 0);
}

/**
 * Erzeugt aus einer Gruppe (oder einer Auswahl daraus) eine gemeinsame
 * Wartungsanfrage, die per E-Mail an den Hersteller geht. Intern bleiben die
 * einzelnen Wartungsaufträge separat (siehe createMaintenanceRequest).
 */
export function buildRequestFromGroup(db, { manufacturerId, orderIds, emailThreadId = null }) {
  return createMaintenanceRequest(db, { manufacturerId, orderIds, emailThreadId });
}
