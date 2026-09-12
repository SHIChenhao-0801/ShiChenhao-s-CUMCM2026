"""Read-only source fidelity audit; writes only task QA reports."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
QA = Path(__file__).resolve().parent
DOCX = ROOT / 'paper_output/final_paper.docx'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def paragraph_text(paragraph):
    parts = []
    for child in paragraph.iter():
        if child.tag == W + 't':
            parts.append(child.text or '')
        elif child.tag == W + 'tab':
            parts.append('\t')
        elif child.tag in (W + 'br', W + 'cr'):
            parts.append('\n')
    return ''.join(parts)

def main():
    docx_bytes = DOCX.read_bytes()
    manifests = [QA / 'code_appendix_manifest.json', QA / 'verification_code_appendix_manifest.json']
    entries = []
    manifest_records = []
    for manifest_path in manifests:
        data = manifest_path.read_bytes()
        manifest_records.append({'path': str(manifest_path), 'sha256': digest(data)})
        entries.extend(json.loads(data.decode('utf-8-sig'))['files'])
    with zipfile.ZipFile(DOCX) as archive:
        tree = ET.fromstring(archive.read('word/document.xml'))
    paragraphs = tree.findall('.//' + W + 'p')
    blocks = []
    for i, paragraph in enumerate(paragraphs):
        if paragraph.get(W + 'rsidR') == '00000001':
            if i == 0 or paragraphs[i-1].get(W + 'rsidR') != '00000001':
                blocks.append({'startParagraphOneBased': i + 1,
                    'precedingParagraphs': [paragraph_text(p) for p in paragraphs[max(0, i-5):i]
                        if p.get(W + 'rsidR') != '00000001'],
                    'lines': []})
            blocks[-1]['lines'].append(paragraph_text(paragraph))
    checks = []
    for index, entry in enumerate(entries):
        source_path = ROOT / entry['path']
        raw = source_path.read_bytes()
        source_lines = raw.decode('utf-8-sig').splitlines()
        block = blocks[index] if index < len(blocks) else {'lines': [], 'precedingParagraphs': []}
        actual_lines = block['lines']
        mismatch = []
        for line_index in range(max(len(source_lines), len(actual_lines))):
            expected = source_lines[line_index] if line_index < len(source_lines) else None
            actual = actual_lines[line_index] if line_index < len(actual_lines) else None
            if expected != actual:
                mismatch.append({'lineOneBased': line_index + 1, 'source': expected, 'docx': actual})
        checks.append({'order': index + 1, 'path': str(source_path),
            'sourceSha256': digest(raw), 'manifestSha256': entry['sha256'],
            'rawHashMatches': digest(raw) == entry['sha256'],
            'manifestLineCount': entry['lineCount'], 'sourceLineCount': len(source_lines),
            'docxLineCount': len(actual_lines), 'lineCountMatches': len(source_lines) == len(actual_lines) == entry['lineCount'],
            'allLinesExactlyMatch': not mismatch,
            'mismatchCount': len(mismatch), 'mismatches': mismatch,
            'docxStartParagraphOneBased': block.get('startParagraphOneBased'),
            'precedingParagraphs': block['precedingParagraphs'],
            'headingMatchesFilename': any(entry['name'] in p for p in block['precedingParagraphs']),
            'sourceShaPrintedInDocument': any(entry['sha256'] in p for p in block['precedingParagraphs']),
            'sourceNormalizedLinesSha256': digest('\n'.join(source_lines).encode('utf-8')),
            'docxNormalizedLinesSha256': digest('\n'.join(actual_lines).encode('utf-8'))})
    passed = len(entries) == len(blocks) == 42 and sum(len(b['lines']) for b in blocks) == 9434 and all(
        c['rawHashMatches'] and c['lineCountMatches'] and c['allLinesExactlyMatch'] and c['headingMatchesFilename'] for c in checks)
    report = {'generatedAtUtc': datetime.now(timezone.utc).isoformat(),
        'status': 'PASS_SOURCE_LINES' if passed else 'FAIL', 'scope': 'DOCX OOXML source-line fidelity only; no model execution, visual readability certification, or human acceptance.',
        'docx': {'path': str(DOCX), 'sha256': digest(docx_bytes)}, 'manifests': manifest_records,
        'method': 'Independent XML read of every w:p with w:rsidR=00000001; contiguous blocks mapped in manifest order. Reconstruct w:t verbatim and w:tab as TAB. Every Unicode source line, whitespace, and empty line compared exactly after UTF-8 BOM removal and splitlines normalization. Raw source hashes independently checked. Printed hashes are optional metadata observations, not a source-fidelity gate. Original BOM and physical newline-byte conventions are not encoded by Word paragraphs and are not claimed recoverable from the DOCX alone.',
        'sourceFileCount': len(entries), 'docxBlockCount': len(blocks), 'docxSourceLineCount': sum(len(b['lines']) for b in blocks),
        'checks': checks, 'docxUnchangedDuringAudit': digest(DOCX.read_bytes()) == digest(docx_bytes)}
    if not report['docxUnchangedDuringAudit']:
        report['status'] = 'FAIL_DOCUMENT_CHANGED'
    (QA / 'docx_embedded_source_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    rows = ['# DOCX 内嵌源码逐行复原核查', '', f"状态：{report['status']}。共 {len(entries)} 份源码、{report['docxSourceLineCount']} 行。", '',
        f"DOCX SHA256：`{digest(docx_bytes)}`。", '',
        '逐段重建 OOXML 中带指定 rsidR 的代码文字，与两份 manifest 顺序、源码原始 SHA256、文件标题及所印 SHA256 核对；空白行、缩进、TAB 均逐行比较。只规范化文本编码 BOM 与物理换行约定，未删除任何代码行。Word 段落本身不保存源文件 BOM 和 CRLF/LF 字节约定，因此此 PASS 是全文逐行一致，不宣称单靠 DOCX 可恢复原始文件字节格式。', '',
        '| 次序 | 文件 | 行数 | 源码哈希 | 逐行内容 |', '|---:|---|---:|---|---|']
    rows.extend(f"| {c['order']} | {Path(c['path']).name} | {c['docxLineCount']} | {'匹配' if c['rawHashMatches'] else '不匹配'} | {'全部一致' if c['allLinesExactlyMatch'] else '不一致'} |" for c in checks)
    rows.extend(['', '本次未运行 PDE、未编辑 DOCX 或源码；本报告不替代逐页视觉检查和团队人工审查。'])
    (QA / 'docx_embedded_source_audit.md').write_text('\n'.join(rows) + '\n', encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','sourceFileCount','docxBlockCount','docxSourceLineCount','docxUnchangedDuringAudit']}, ensure_ascii=False))
    raise SystemExit(0 if report['status'] == 'PASS_SOURCE_LINES' else 1)

if __name__ == '__main__':
    main()
