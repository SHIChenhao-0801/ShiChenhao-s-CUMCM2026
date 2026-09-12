"""Read-only retrieval of publication evidence; no manuscript/model mutation."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib, json, urllib.request, urllib.parse

ROOT = Path(__file__).resolve().parent
DOIS = {
    'wang_2024': '10.11975/j.issn.1002-6819.202306104',
    'wang_2023': '10.19540/j.cnki.cjcmm.20230331.301',
    'eymard_2000': '10.1016/S1570-8659(00)07005-8',
    'shampine_1997': '10.1137/S1064827594276424',
    'mujumdar_2014': '10.1201/b17208',
}
SOURCES = {
    'wang_2023_publisher.pdf': 'https://www.tcmjc.com/download/pdf?id=2758B0FBE5314A1ABD31D280D6B915B3',
    'crank_1975_bath.pdf': 'https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf',
    'eymard_author.pdf': 'https://www.i2m.univ-amu.fr/perso/raphaele.herbin/PUBLI/bookevol.pdf',
    'mujumdar_preview.pdf': 'https://api.pageplace.de/preview/DT0400.9781466596665_A24035542/preview-9781466596665_A24035542.pdf',
    'shampine_byu.pdf': 'https://www.et.byu.edu/~beard/papers/library/MatlabOdeSuite.pdf',
}
def fetch(item):
    name,url=item
    record={'name':name,'url':url,'retrieved_utc':datetime.now(timezone.utc).isoformat()}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (academic bibliography verification)'})
        with urllib.request.urlopen(req, timeout=35) as r:
            data=r.read()
            record.update(status=r.status, final_url=r.url, content_type=r.headers.get('Content-Type'),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        expected_pdf=name.endswith('.pdf')
        if expected_pdf and not data.startswith(b'%PDF'):
            record['valid_pdf']=False
        else:
            p=ROOT/'source_cache'/name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            record['saved_path']=str(p)
            if expected_pdf: record['valid_pdf']=True
        if name.endswith('.json'):
            j=json.loads(data)
            m=j.get('message',{})
            record['metadata']={k:m.get(k) for k in ['DOI','title','author','editor','container-title','volume','issue','page','publisher','published','published-print','published-online','ISBN','URL','type']}
    except Exception as e:
        record['error']=repr(e)
    return record

items=[(name+'.crossref.json','https://api.crossref.org/works/'+urllib.parse.quote(doi,safe='')) for name,doi in DOIS.items()]+list(SOURCES.items())
with ThreadPoolExecutor(max_workers=5) as pool: results=list(pool.map(fetch,items))
(ROOT/'retrieval_evidence.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
for result in results:
    print(json.dumps(result,ensure_ascii=False))
