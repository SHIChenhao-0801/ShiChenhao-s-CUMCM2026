import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';
const root = 'D:/Document/数学建模/2026CUMCM';
const base = `${root}/problem_files/CUMCM2026Problems/A题/附件`;
const out = [];
for (const name of ['附件1.xlsx','附件2.xlsx','附件3/result1.xlsx','附件3/result2.xlsx','附件3/result3.xlsx','附件3/result4.xlsx']) {
  const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(`${base}/${name}`));
  const overview = await wb.inspect({kind:'workbook,sheet,table', maxChars:2400,tableMaxRows:3,tableMaxCols:5});
  const entry = {file:name,sha256:crypto.createHash('sha256').update(await fs.readFile(`${base}/${name}`)).digest('hex'),overview:overview.ndjson};
  if (!name.includes('/')) {
    const rows = wb.worksheets.getItemAt(0).getUsedRange(true).values;
    entry.rows = rows;
    const numeric = rows.filter(r=>typeof r[0]==='number');
    entry.recordCount=numeric.length;
    entry.first=numeric[0];entry.last=numeric.at(-1);
    entry.ranges = numeric[0].map((_,i)=>({column:i,min:Math.min(...numeric.map(r=>r[i])),max:Math.max(...numeric.map(r=>r[i]))}));
    entry.gaps=[...new Set(numeric.slice(1).map((r,i)=>r[0]-numeric[i][0]))];
    entry.missing=numeric.flat().filter(v=>v===null||v==='').length;
    entry.duplicateTimes=numeric.length-new Set(numeric.map(r=>r[0])).size;
    if(name==='附件1.xlsx') {
      const tail=numeric.filter(r=>r[0]>=10800);
      entry.tailHourMeans=numeric[0].map((_,i)=>tail.reduce((s,r)=>s+r[i],0)/tail.length);
      entry.tailHourRanges=numeric[0].map((_,i)=>({min:Math.min(...tail.map(r=>r[i])),max:Math.max(...tail.map(r=>r[i]))}));
    }
    if(name==='附件2.xlsx') entry.radiusIncreases=numeric.slice(1).filter((r,i)=>r[1]>numeric[i][1]).length;
  }
  out.push(entry);
  const {rows,...brief}=entry;
  console.log(JSON.stringify(brief));
}
await fs.writeFile(`${root}/notes/selection-evaluation/2026-09-10/A附件_只读核对.json`,JSON.stringify(out,null,2));
