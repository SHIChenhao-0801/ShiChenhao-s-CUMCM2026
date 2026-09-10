import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';

const root = 'D:/Document/数学建模/2026CUMCM';
const base = `${root}/problem_files/CUMCM2026Problems/A题/附件`;
const output = `${root}/notes/A-modeling/2026-09-10/data`;
const previous = JSON.parse(await fs.readFile(`${root}/notes/selection-evaluation/2026-09-10/A附件_只读核对.json`, 'utf8'));
const stats = values => {
  const mean = values.reduce((a,b) => a+b,0)/values.length;
  return {count:values.length,min:Math.min(...values),max:Math.max(...values),mean,sd:Math.sqrt(values.reduce((a,b)=>a+(b-mean)**2,0)/Math.max(1,values.length-1))};
};
const result = {created_utc:new Date().toISOString(),scope:root,operation:'read-only XLSX import, statistics, schema/hash check; no model solve',reader:'@oai/artifact-tool; Node.js',visual_studio_reproduction:false,human_review:false,assets:[]};
for (const name of ['附件1.xlsx','附件2.xlsx','附件3/result1.xlsx','附件3/result2.xlsx','附件3/result3.xlsx','附件3/result4.xlsx']) {
  const source = `${base}/${name}`;
  const before = crypto.createHash('sha256').update(await fs.readFile(source)).digest('hex');
  const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(source));
  const entry = {file:source,sha256:before,matches_previous_audit:before===previous.find(x=>x.file===name)?.sha256,sheets:[]};
  const nSheets = name.includes('result1')||name.includes('result2') ? 2 : 1;
  for(let s=0;s<nSheets;s++) {
    const sheet=wb.worksheets.getItemAt(s);
    const rows=sheet.getUsedRange(true).values;
    const sheetResult = {name:sheet.name,rows:rows.length,cols:Math.max(...rows.map(r=>r.length)),header:rows[0],values:rows};
    if(!name.includes('/')) {
      const numeric=rows.slice(1);
      const invalid=[];
      numeric.forEach((r,i)=>{for(let j=0;j<rows[0].length;j++)if(typeof r[j]!=='number'||!Number.isFinite(r[j]))invalid.push({row:i+2,col:j+1,value:r[j]??null});});
      Object.assign(sheetResult,{recordCount:numeric.length,first:numeric[0],last:numeric.at(-1),columns:rows[0].map((n,j)=>({name:n,index:j,...stats(numeric.map(r=>r[j]))})),invalid_numeric_cells:invalid,duplicate_time_count:numeric.length-new Set(numeric.map(r=>r[0])).size,time_steps_s:[...new Set(numeric.slice(1).map((r,i)=>r[0]-numeric[i][0]))]});
      if(name==='附件1.xlsx') {
        sheetResult.units = ['s','°C','kg/kg (air; denominator not explicitly identified in statement)'];
        sheetResult.tail_3_to_4h = {start_s:10800,end_s:14400,temperature:stats(numeric.filter(r=>r[0]>=10800).map(r=>r[1])),air_moisture:stats(numeric.filter(r=>r[0]>=10800).map(r=>r[2]))};
        sheetResult.local_decreases = [1,2].map(j=>({column:j,count:numeric.slice(1).filter((r,i)=>r[j]<numeric[i][j]).length}));
        sheetResult.observation_support_until_s=14400;
      } else {
        sheetResult.units=['s','cm'];
        sheetResult.radius_increases=numeric.slice(1).filter((r,i)=>r[1]>numeric[i][1]).length;
        sheetResult.tail_48_to_72h=stats(numeric.filter(r=>r[0]>=172800).map(r=>r[1]));
        sheetResult.radius_decrements_cm=[...new Set(numeric.slice(1).map((r,i)=>Number((r[1]-numeric[i][1]).toFixed(6))))].sort((a,b)=>a-b);
        sheetResult.observation_support_until_s=259200;
      }
    }
    entry.sheets.push(sheetResult);
  }
  entry.unchanged_after_read=before===crypto.createHash('sha256').update(await fs.readFile(source)).digest('hex');
  result.assets.push(entry);
}
result.support_limits={room_boundary_observed_s:[0,14400],radius_observed_s:[0,259200],internal_temperature_measurements:false,internal_moisture_measurements:false,latent_heat_or_sorption_parameters:false,axial_shrinkage_measurements:false,replicates_or_measurement_uncertainty:false};
result.assumptions=[{id:'A-interpolation',start:'between every pair of measured samples',baseline:'piecewise linear interpolation',status:'modeling convention, not observation'},{id:'A-air_to_solid',start:'surface mass-transfer boundary at t=0',baseline:'effective concentration Robin closure only with explicit same-scale convention',status:'air kg/kg is not inherently equal to dry-basis solid kg/kg; sorption data unavailable'},{id:'A-long_environment',start_s:14400,baseline:'constant 50 °C and air indicator 0.05 kg/kg',alternatives:['last measured sample','3–4 h means','tail observed extrema and wider process scenarios'],status:'extrapolation assumption, not measured or proved steady'},{id:'A-shrink_motion',start_s:0,baseline:'prescribed R(t), axial length constant and radial affine material velocity',status:'only R(t) observed; interior velocity and length are assumptions'},{id:'A-long_radius',start_s:259200,baseline:'hold R(72h)=1.198 cm',alternatives:['positive monotone asymptotic fit','bounded tail continuation stress test'],status:'required only if drying has not ended by 72 h'}];
await fs.writeFile(`${output}/input_audit.json`,JSON.stringify(result,null,2));
for(const a of result.assets) console.log(JSON.stringify({...a,sheets:a.sheets.map(({values,...s})=>s)}));
