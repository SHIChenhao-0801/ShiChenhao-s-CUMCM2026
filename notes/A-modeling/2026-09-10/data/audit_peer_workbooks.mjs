import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';

// Own read-only importer. Never imports peer Python or opens pickle objects.
const root='D:/Document/数学建模/2026CUMCM';
const peer=root+'/reference_materials/peer-models/2026-09-10_A_model';
const out=root+'/notes/A-modeling/2026-09-10/data';
const summary=JSON.parse(await fs.readFile(peer+'/out/summary.json','utf8'));
const radius=(await fs.readFile(root+'/paper_output/data_cleaned/A_radius_observed.csv','utf8'))
 .replace(/^\uFEFF/,'').trim().split(/\r?\n/).slice(1).map(s=>s.split(',').map(Number));
function Rcm(t) {
 let i=0; while(i<radius.length-2 && radius[i+1][0]<t) i++;
 if(t<=radius[0][0])return radius[0][2];
 if(t>=radius.at(-1)[0])return radius.at(-1)[2];
 const f=(t-radius[i][0])/(radius[i+1][0]-radius[i][0]);
 return radius[i][2]*(1-f)+radius[i+1][2]*f;
}
const sha=async p=>crypto.createHash('sha256').update(await fs.readFile(p)).digest('hex');
const result={created_utc:new Date().toISOString(),reader:'bundled Node @oai/artifact-tool',
 operation:'read-only XLSX import and independent value/schema checks',
 peer_code_executed:false,pickle_loaded:false,assets:[],cross_checks:{}};
const cache={};
for(let q=1;q<=4;q++) {
 const path=peer+'/out/result'+q+'.xlsx';
 const before=await sha(path);
 const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
 const asset={question:q,path,sha256:before,bytes:(await fs.stat(path)).size,sheets:[]};
 for(let sn=0;sn<(q<=2?2:1);sn++) {
  const sheet=wb.worksheets.getItemAt(sn);
  const rows=sheet.getUsedRange(true).values;
  const header=rows[0], data=rows.slice(1), times=data.map(r=>r[0]);
  cache[q+'_'+sn]=data;
  let invalid=0, missing=0, outside=0, outsideFilled=0, insideBlank=0, badPrecision=0;
  let vmin=Infinity,vmax=-Infinity;
  const errExamples=[];
  let radialIncreasing=0,zeroCount=0,surfaceDuplicates=0,surfaceMismatch=0;
  for(let i=0;i<data.length;i++) {
   const row=data[i],t=row[0],R=q===4?Rcm(t):2;
   for(let col=1;col<header.length;col++) {
    const v=row[col],isBlank=v===null||v===undefined||v==='';
    const radial=typeof header[col]==='number';
    const isOutside=radial && header[col]>R+1e-9;
    if(isOutside) {
     outside++;
     if(!isBlank) {outsideFilled++; if(errExamples.length<8)errExamples.push({row:i+2,col:col+1,t,R,value:v,type:'outside_filled'});}
    } else if(isBlank) {insideBlank++; if(errExamples.length<8)errExamples.push({row:i+2,col:col+1,t,R,type:'inside_blank'});}
    if(isBlank) {missing++; continue;}
    if(typeof v!=='number'||!Number.isFinite(v)){invalid++;continue;}
    vmin=Math.min(vmin,v);vmax=Math.max(vmax,v);if(v===0)zeroCount++;
    if(Math.abs(v*1e4-Math.round(v*1e4))>1e-6)badPrecision++;
    if(radial && col>=2 && typeof row[col-1]==='number' && v>row[col-1]+1e-10 && !(q<=2&&sn===0))radialIncreasing++;
   }
   if(q===4) {
    const surface=row[header.length-1];
    const j=header.findIndex(h=>typeof h==='number'&&Math.abs(h-R)<1e-9);
    if(j>0){surfaceDuplicates++;if(row[j]!==surface)surfaceMismatch++;}
   }
  }
  const steps={};
  for(let i=1;i<times.length;i++){const d=times[i]-times[i-1];steps[d]=(steps[d]||0)+1;}
  const critical=q>=3?summary['q'+q].T_star_s:null;
  const earliestGrid=critical===null?null:Math.floor(critical/60+1)*60;
  const near=critical===null?[]:data.filter(r=>Math.abs(r[0]-critical)<=180)
       .map((r)=>({excel_row:times.indexOf(r[0])+2,time_s:r[0],center_C:r[1],surface_C:r.at(-1)}));
  const rec={sheet:sheet.name,used_rows:rows.length,data_rows:data.length,columns:header.length,
   header,first:data[0],last:data.at(-1),times:{first:times[0],last:times.at(-1),step_counts:steps,
   duplicate_count:times.length-new Set(times).size,noninteger_count:times.filter(t=>!Number.isInteger(t)).length},
   numeric:{min:vmin,max:vmax,invalid_count:invalid,blank_count:missing,non_four_decimal_rounded:badPrecision,zero_count:zeroCount},
   geometry:{outside_expected:outside,outside_filled:outsideFilled,inside_blank:insideBlank,
   radial_C_increase_count:radialIncreasing,surface_equals_grid_count:surfaceDuplicates,surface_grid_mismatch:surfaceMismatch,examples:errExamples},
   event:critical===null?null:{reported_critical_s:critical,first_60s_grid_after_critical:earliestGrid,
   actual_end_s:times.at(-1),extra_seconds_after_first_grid:times.at(-1)-earliestGrid,
   rows_near_critical:near,first_saved_rounded_max_below_015:data.find(r=>Math.max(...r.slice(1).filter(v=>typeof v==='number'))<.15)?.[0]??null}};
  asset.sheets.push(rec);
 }
 asset.unchanged_after_read=(await sha(path))===before;
 result.assets.push(asset);
 console.log(JSON.stringify({q,rows:asset.sheets.map(s=>({sheet:s.sheet,rows:s.data_rows,end:s.times.last,outside_filled:s.geometry.outside_filled,inside_blank:s.geometry.inside_blank,event:s.event}))}));
}
const q2=new Map(cache['2_1'].map(row=>[row[0],row]));
let shared=0,maxdelta=0,diffcells=0,where=null;
for(const row of cache['3_0'])if(q2.has(row[0])) {
 shared++;const old=q2.get(row[0]);
 for(let j=1;j<22;j++){const diff=Math.abs(old[j]-row[j]);if(diff>1e-12)diffcells++;if(diff>maxdelta){maxdelta=diff;where={time_s:row[0],radius_cm:(j-1)/10,q2:old[j],q3:row[j]};}}
}
result.cross_checks.q2_q3_shared_rounded_cells={shared_times:shared,compared_cells:shared*21,different_cells:diffcells,max_abs_difference:maxdelta,where};
await fs.writeFile(out+'/peer_workbook_audit.json',JSON.stringify(result,null,2));
console.log(JSON.stringify(result.cross_checks));
