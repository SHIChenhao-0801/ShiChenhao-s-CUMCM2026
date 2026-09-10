import fs from 'node:fs/promises';
import path from 'node:path';
import readline from 'node:readline';
import {createReadStream} from 'node:fs';
const root='D:/Document/数学建模';
const sessionDir='C:/Users/Shi Chenhao/.codex/sessions/2026/09/10';
const out=`${root}/2026CUMCM/notes/A-modeling/2026-09-10/data`;
const normalize=p=>String(p??'').replaceAll('\\','/').replace(/\/$/,'').toLowerCase();
const report={created_utc:new Date().toISOString(),scope:root,note:'Only first session_meta checked before reading body; only matching workspace and descendants inspected. Matched user and assistant visible messages, not tool records or private reasoning.',sessions:[],matches:[]};
for(const name of await fs.readdir(sessionDir)) {
  if(!name.endsWith('.jsonl'))continue;
  const file=path.join(sessionDir,name);
  const lineReader=readline.createInterface({input:createReadStream(file),crlfDelay:Infinity});
  let first;
  for await(const line of lineReader){first=JSON.parse(line);break;}
  lineReader.close();
  const meta=first?.type==='session_meta'?first.payload:null;
  if(!meta||!(normalize(meta.cwd)===normalize(root)||normalize(meta.cwd).startsWith(normalize(root)+'/')))continue;
  report.sessions.push({id:meta.id,cwd:meta.cwd,path:file});
  // Avoid the present task and its children self-matching search strings.
  if(String(meta.timestamp??'')>='2026-09-10T13:42:00')continue;
  const contents=await fs.readFile(file,'utf8');
  for(const line of contents.split('\n')) {
    if(!line.trim())continue;
    const event=JSON.parse(line);
    if(event.type!=='response_item'||event.payload?.type!=='message'||!['user','assistant'].includes(event.payload.role))continue;
    if(event.payload.channel==='analysis')continue;
    const text=(event.payload.content??[]).filter(x=>['input_text','output_text','text'].includes(x.type)).map(x=>x.text??'').join('\n');
    const keys=[...text.matchAll(/N\s*=\s*400|Bessel|仿射收缩|生产计算|统一数学模型|autoresponse|全部公式|所有公式/g)].map(m=>m[0]);
    if(!keys.length)continue;
    report.matches.push({session:meta.id,path:file,timestamp:event.timestamp,role:event.payload.role,channel:event.payload.channel,keywords:[...new Set(keys)],excerpt:text.length>18000?text.slice(0,18000):text});
  }
}
await fs.writeFile(`${out}/project_history_matches.json`,JSON.stringify(report,null,2));
console.log(JSON.stringify({sessions:report.sessions.length,matches:report.matches.map(({excerpt,...x})=>x)}));
