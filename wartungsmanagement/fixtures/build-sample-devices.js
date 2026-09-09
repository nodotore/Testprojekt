import ExcelJS from 'exceljs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));

const ROWS = [
  ['Fresenius', 'Dialysegerät', '5008 CorDiax', 'MT-1001', '12345', 'Dialyse', '20.09.2026'],
  ['Fresenius', 'Dialysegerät', '5008 CorDiax', 'MT-1002', '12346', 'Dialyse', '22.09.2026'],
  ['Fresenius', 'Wasseraufbereitung', 'AquaA', 'MT-2050', '94832', 'Dialyse', '25.09.2026'],
  ['Firma A', 'Patientenmonitor', 'Modell X', 'INV-001', 'SN-001', 'Intensivstation', '01.10.2026'],
  ['Firma A', 'Patientenmonitor', 'Modell X', 'INV-002', 'SN-002', 'Intensivstation', '03.10.2026'],
];

export async function buildSampleWorkbook(path = join(__dirname, 'sample-devices.xlsx')) {
  const workbook = new ExcelJS.Workbook();
  const sheet = workbook.addWorksheet('Geräte');
  sheet.addRow(['Hersteller', 'Gerätetyp', 'Gerät', 'Inventarnummer', 'Seriennummer', 'Standort', 'Wartung fällig']);
  for (const row of ROWS) sheet.addRow(row);
  await workbook.xlsx.writeFile(path);
  return path;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const path = await buildSampleWorkbook();
  console.log(`Beispiel-Excel geschrieben: ${path}`);
}
