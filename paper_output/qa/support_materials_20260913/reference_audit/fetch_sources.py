"""Archive public primary sources for the supporting reference folder."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib, json, urllib.request

HERE = Path(__file__).resolve().parent
RAW = HERE / 'raw_downloads'
RAW.mkdir(parents=True, exist_ok=True)
ITEMS = [
 ('wang2024_publisher.html','https://nygcxb.ijournals.cn/nygcxb/article/abstract/20240201'),
 ('wang2024_full.pdf','https://www.aeeisp.com/nygcxb/cn/article/pdf/preview/10.11975/j.issn.1002-6819.202306104.pdf'),
 ('wang2023_publisher.pdf','https://www.tcmjc.com/download/pdf?id=2758B0FBE5314A1ABD31D280D6B915B3'),
 ('wang2023_pubmed.html','https://pubmed.ncbi.nlm.nih.gov/37474981/'),
 ('wang2023_pubmed.xml','https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=37474981&retmode=xml'),
 ('mujumdar_publisher.html','https://www.routledge.com/Handbook-of-Industrial-Drying/Mujumdar/p/book/9781466596658'),
 ('crank_ndl.html','https://ndlsearch.ndl.go.jp/books/R100000074-IALIS_QQ00223544'),
 ('scipy_bdf.html','https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.BDF.html'),
 ('fao_drying.html','https://www.fao.org/4/t1838e/t1838e0u.htm'),
 ('scipy_solve_ivp.html','https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html'),
 ('sundials_references.html','https://sundials.readthedocs.io/en/v7.1.0/References.html'),
]
def fetch(item):
    name,url = item
    r={'file':name,'url':url,'retrieved_utc':datetime.now(timezone.utc).isoformat()}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (bibliographic evidence archive)'})
        with urllib.request.urlopen(req,timeout=30) as resp:
            data=resp.read(25_000_000)
            r.update(status=resp.status,final_url=resp.url,content_type=resp.headers.get('Content-Type'),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        if name.endswith('.pdf') and not data.startswith(b'%PDF'):
            r['accepted']=False
            r['reason']='Response does not contain a PDF file; not saved as a PDF.'
        elif not data:
            r['accepted']=False
            r['reason']='Empty response.'
        else:
            (RAW/name).write_bytes(data)
            r['accepted']=True
    except Exception as exc:
        r.update(accepted=False,error=str(exc))
    return r
with ThreadPoolExecutor(max_workers=5) as pool:
    results=list(pool.map(fetch,ITEMS))
(HERE/'retrieval_evidence.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False,indent=2))
