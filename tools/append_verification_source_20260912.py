"""Append complete adopted verification sources with version and scope notes."""
from pathlib import Path
import hashlib
import json

root=Path(__file__).resolve().parents[1]
assert Path.cwd().resolve()==root
qa=root/'paper_output/qa/manuscript_20260912'
target=root/'paper_output/drafts/sections/appendix.md'
text=target.read_text(encoding='utf-8')
marker='\n## E 验证程序与历史版本完整清单\n'
text=text.split(marker)[0].rstrip()
records=json.loads((qa/'verification_code_appendix_manifest.json').read_text(encoding='utf-8'))['files']
parts=[text,marker,'本节给出正文及本附录实际采用的检验程序、相应历史求解器和运行依赖，共31份、6440行；与附录D的11份、2994行合计42份、9434行。历史源码按证据原样保留，各文件前的采用范围和勘误限定其在本稿中的用途。历史验证与当前生产结果使用不同版本时，须按所列原运行槽位组织文件，不能任意混用。\n']
for i,rec in enumerate(records,1):
    raw=(root/rec['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==rec['sha256']
    source=raw.decode('utf-8-sig')
    assert len(source.splitlines())==rec['lineCount']
    parts += [f"### E.{i} {rec['name']}：{rec['role']}\n",
              f"文件：`{rec['path']}`；共{rec['lineCount']}行。采用范围：{rec['adoptedScope']}\n"]
    if rec.get('note'):parts.append('版本说明与勘误：'+rec['note']+'\n')
    if rec.get('originalRuntimeSlot') and rec['originalRuntimeSlot']!=rec['path']:
        parts.append('原运行槽位：`'+rec['originalRuntimeSlot']+'`。\n')
    suffix=Path(rec['path']).suffix
    lang={'.py':'python','.m':'matlab','.mjs':'javascript','.ps1':'powershell'}.get(suffix,'text')
    parts += ['```'+lang+'\n'+'\n'.join(source.splitlines())+'\n```\n']
target.write_text('\n'.join(parts),encoding='utf-8')
print(json.dumps({'files':len(records),'lines':sum(x['lineCount'] for x in records),'appendixBytes':target.stat().st_size}))
