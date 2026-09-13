from pathlib import Path
import os, sys, json, hashlib, subprocess
import pymupdf

ROOT = Path.cwd()
assert ROOT.as_posix() == 'D:/Document/数学建模/2026CUMCM'
sys.stdout.reconfigure(encoding='utf-8')
QA = ROOT / 'paper_output/qa/appendix_revision_20260913'
source, version = Path(sys.argv[1]).resolve(), sys.argv[2]
render = ROOT / 'tmp/cache/appendix_revision_20260913' / version
render.mkdir(parents=True, exist_ok=True)
temp = render.parent / 'temp'
temp.mkdir(exist_ok=True)
env = os.environ.copy()
runtime = Path(sys.executable).parent.parent
# User-authorized project-local portable runtime. On Windows the bundled
# renderer explicitly resolves native soffice.exe; the runtime bundles no LO.
lo = ROOT.parent / 'tools/libreoffice/app/program'
assert (lo / 'soffice.exe').exists()
env['PATH'] = str(lo) + os.pathsep + str(runtime / 'native/poppler/Library/bin') + os.pathsep + env['PATH']
for key in ('TEMP', 'TMP', 'TMPDIR'):
    env[key] = str(temp)
env['PYTHONIOENCODING'] = 'utf-8'
renderer = 'C:/Users/Shi Chenhao/.codex/plugins/cache/openai-primary-runtime/documents/26.905.11957/skills/documents/render_docx.py'
with (QA / (version + '_render.log')).open('w', encoding='utf-8') as log:
    proc = subprocess.run([sys.executable, '-B', renderer, str(source), '--output_dir', str(render), '--emit_pdf', '--dpi', '110', '--verbose'], cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
assert proc.returncode == 0, proc.returncode
pdf = render / (source.stem + '.pdf')
doc = pymupdf.open(pdf)
pages = []
for i, page in enumerate(doc, 1):
    image = render / f'page-{i}.png'
    assert image.exists()
    spans = [s for b in page.get_text('dict')['blocks'] if 'lines' in b for line in b['lines'] for s in line['spans']]
    suspects = [{'text': s['text'], 'bbox': s['bbox']} for s in spans if s['bbox'][0] < 30 or s['bbox'][2] > page.rect.width - 25 or s['bbox'][1] < 20 or s['bbox'][3] > page.rect.height - 10]
    pages.append({'page': i, 'image': image.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(image.read_bytes()).hexdigest(), 'text': page.get_text(), 'geometry_suspects': suspects})
manifest = {'docx': source.relative_to(ROOT).as_posix(), 'docx_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'pdf': pdf.relative_to(ROOT).as_posix(), 'page_count': len(doc), 'pages': pages, 'render_exit_code': proc.returncode}
(QA / (version + '_render_manifest.json')).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'version': version, 'pages': len(doc), 'geometry_suspect_pages': [p['page'] for p in pages if p['geometry_suspects']]}, ensure_ascii=False))
