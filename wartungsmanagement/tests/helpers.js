import { openDatabase } from '../src/db/db.js';
import { getOrCreateManufacturer } from '../src/models/manufacturers.js';
import { getOrCreateDevice } from '../src/models/devices.js';
import { createMaintenanceOrder } from '../src/models/maintenanceOrders.js';

export function setupDb() {
  return openDatabase(':memory:');
}

export function seedFreseniusExample(db) {
  const manufacturer = getOrCreateManufacturer(db, 'Fresenius');
  const devices = [
    { deviceType: 'Dialysegerät', model: '5008 CorDiax', inventoryNumber: 'MT-1001', serialNumber: '12345', nextMaintenanceDue: '2026-09-20' },
    { deviceType: 'Dialysegerät', model: '5008 CorDiax', inventoryNumber: 'MT-1002', serialNumber: '12346', nextMaintenanceDue: '2026-09-22' },
    { deviceType: 'Wasseraufbereitung', model: 'AquaA', inventoryNumber: 'MT-2050', serialNumber: '94832', nextMaintenanceDue: '2026-09-25' },
  ].map((d) => getOrCreateDevice(db, { manufacturerId: manufacturer.id, ...d }));

  const orders = devices.map((device) =>
    createMaintenanceOrder(db, {
      deviceId: device.id,
      manufacturerId: manufacturer.id,
      dueDate: device.next_maintenance_due,
    })
  );

  return { manufacturer, devices, orders };
}
