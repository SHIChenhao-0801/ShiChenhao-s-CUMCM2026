import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';

const outputDir = path.dirname(fileURLToPath(import.meta.url));
const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(outputDir, 'result1.xlsx')));
wb.recalculate();
const inspection = await wb.inspect({kind:'region', sheetId:'温度', range:'A1:H8', maxChars:3000});
await fs.writeFile(path.join(outputDir, 'saved_workbook_inspection.ndjson'), inspection.ndjson);
for (const [sheetName, fileName] of [['温度','temperature_saved_preview.png'],['水分浓度','moisture_saved_preview.png']]) {
  const preview = await wb.render({sheetName,range:'A1:H8',scale:1.5,format:'png'});
  await fs.writeFile(path.join(outputDir,fileName),new Uint8Array(await preview.arrayBuffer()));
}
console.log('Rendered the first eight rows of both saved Q1 worksheets.');
