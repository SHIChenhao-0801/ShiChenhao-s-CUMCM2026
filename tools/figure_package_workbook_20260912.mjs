import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

// Exports frozen plotting data only. No model calculations or fitting occur here.
const root = path.resolve(process.cwd());
if (!root.replaceAll('\\', '/').endsWith('/数学建模/2026CUMCM')) throw new Error('Wrong workspace');
const cache = path.join(root, 'tmp/cache/figure_package_20260912/workbook');
const qa = path.join(root, 'paper_output/qa/figure_package_20260912');
const out = path.join(root, 'paper_output/handoff/six_figures_20260912/六图绘图数据.xlsx');
const input = path.join(root, 'tmp/cache/figure_package_20260912/workbook_data.json');
const require = createRequire(path.join(cache, 'package.json'));
const { Workbook, SpreadsheetFile } = await import(pathToFileURL(require.resolve('@oai/artifact-tool')));
await fs.mkdir(cache, { recursive: true });
await fs.mkdir(qa, { recursive: true });
await fs.mkdir(path.dirname(out), { recursive: true });
const data = JSON.parse(await fs.readFile(input, 'utf8'));
const workbook = Workbook.create();
const manifest = { status: 'BUILDING', task: 'six_figure_portable_data', input, out, sheets: [], recalculate: false };
const inspections = [];
const renderOnly = process.env.FIGURE_WORKBOOK_RENDER_ONLY ? new Set(process.env.FIGURE_WORKBOOK_RENDER_ONLY.split(',')) : null;
const previous = renderOnly ? JSON.parse(await fs.readFile(path.join(qa, 'workbook_build_manifest.json'), 'utf8')) : null;
const letters = n => { let s = ''; for (; n > 0; n = Math.floor((n - 1) / 26)) s = String.fromCharCode(65 + (n - 1) % 26) + s; return s; };
const sha = v => crypto.createHash('sha256').update(v).digest('hex');

for (let k = 0; k < data.sheets.length; k++) {
  const spec = data.sheets[k];
  if (!spec.columns.length || spec.rows.some(r => r.length !== spec.columns.length)) throw new Error(`Bad shape ${spec.name}`);
  if (spec.name.length > 31 || /[\\/?*:\[\]]/.test(spec.name)) throw new Error(`Invalid sheet ${spec.name}`);
  const sheet = workbook.worksheets.add(spec.name);
  sheet.showGridLines = false;
  const end = letters(spec.columns.length);
  const viewEnd = letters(Math.max(8, spec.columns.length));
  const last = spec.rows.length + 6;
  const used = sheet.getRange(`A1:${viewEnd}${Math.max(last, 13)}`);
  used.format.font = { name: 'Arial', size: 11, color: '#20252B' };
  used.format.verticalAlignment = 'center';
  used.format.rowHeight = 20;
  used.format.columnWidth = 23;
  sheet.getRange('A1').values = [[spec.title]];
  sheet.getRange(`A1:${viewEnd}1`).format.font = { name: 'Arial', size: 16, bold: true, color: '#20252B' };
  sheet.getRange(`A1:${viewEnd}1`).format.rowHeight = 31;
  sheet.getRange(`A1:${viewEnd}1`).format.borders = { bottom: { style: 'thin', color: '#AAB1BA' } };
  sheet.getRange('A2').values = [[spec.note || '']];
  sheet.getRange('A3').values = [['数值按冻结结果完整导出；显示位数不改变底层精度。空白表示无适用数值，不等于零。']];
  sheet.getRange('A4').values = [[`对应包内文件：${Array.isArray(spec.csv) ? spec.csv.join('；') : spec.csv || ''}`]];
  sheet.getRange(`A2:${viewEnd}4`).format.font = { name: 'Arial', size: 10, color: '#4F5964' };
  sheet.getRange(`A2:${viewEnd}4`).format.rowHeight = 23;
  sheet.getRange(`A2:${viewEnd}4`).format.wrapText = false;
  sheet.getRange(`A5:${viewEnd}5`).format.rowHeight = 9;
  const header = sheet.getRange(`A6:${end}6`);
  header.values = [spec.columns];
  header.format.fill = '#37485B';
  header.format.font = { name: 'Arial', size: 11, bold: true, color: '#FFFFFF' };
  header.format.horizontalAlignment = 'center';
  header.format.wrapText = true;
  header.format.rowHeight = 43;
  header.format.borders = { insideVertical: { style: 'thin', color: '#FFFFFF' } };
  if (spec.rows.length) sheet.getRange(`A7:${end}${last}`).values = spec.rows;
  for (let c = 0; c < spec.columns.length; c++) {
    const l = letters(c + 1);
    const label = spec.columns[c];
    const vals = spec.rows.map(r => r[c]).filter(v => v !== null && v !== '');
    const numeric = vals.length > 0 && vals.every(v => typeof v === 'number');
    const wide = label.length > 24 || /delta|差|gap|interval|coordinate/.test(label);
    sheet.getRange(`${l}1:${l}${Math.max(last, 13)}`).format.columnWidth = label === 'centre_C_minus_threshold' ? 29 : (wide ? 28 : 23);
    if (!spec.rows.length) continue;
    const body = sheet.getRange(`${l}7:${l}${last}`);
    body.format.horizontalAlignment = numeric ? 'right' : 'left';
    if (numeric) {
      const scientific = /delta|minus_threshold|Δ|差|gap/i.test(label) || vals.some(v => Math.abs(v) > 0 && Math.abs(v) < 1e-8);
      body.setNumberFormat(scientific ? '0.000000000000E+00' : (vals.every(Number.isInteger) ? '0' : '0.000000000000'));
    } else {
      const len = Math.max(label.length, ...vals.map(v => String(v).length));
      if (len > 24) sheet.getRange(`${l}1:${l}${Math.max(last, 13)}`).format.columnWidth = Math.min(52, len + 3);
    }
  }
  if (spec.rows.length > 20) sheet.freezePanes.freezeRows(6);
  sheet.tabColor = ['#37485B', '#536D82', '#5E7783', '#536977', '#647586', '#475E76'][Math.max(0, (Number((spec.name.match(/[1-6]/) || [1])[0]) - 1))];
  manifest.sheets.push({ name: spec.name, rows: spec.rows.length, columns: spec.columns, dataRange: `A7:${end}${last}`, source: spec.source, csv: spec.csv, renderedRange: `A1:${viewEnd}${Math.min(last, 15)}` });
}

workbook.recalculate();
manifest.recalculate = true;
for (let k = 0; k < data.sheets.length; k++) {
  const spec = data.sheets[k], meta = manifest.sheets[k];
  const sheet = workbook.worksheets.getItem(spec.name);
  const actual = spec.rows.length ? sheet.getRange(meta.dataRange).values : [];
  if (JSON.stringify(actual) !== JSON.stringify(spec.rows)) throw new Error(`Artifact values mismatch ${spec.name}`);
  const inspection = await workbook.inspect({ kind: 'table', sheetId: spec.name, range: `A6:${letters(spec.columns.length)}${Math.min(spec.rows.length + 6, 10)}`, include: 'values,formulas', tableMaxRows: 5, tableMaxCols: spec.columns.length, maxChars: 3200 });
  inspections.push({ sheet: spec.name, ndjson: inspection.ndjson });
  if (!renderOnly || renderOnly.has(spec.name)) {
    const preview = await workbook.render({ sheetName: spec.name, range: meta.renderedRange, scale: 1.3, format: 'png' });
    const bytes = new Uint8Array(await preview.arrayBuffer());
    const filename = `${String(k + 1).padStart(2, '0')}_${spec.name}.png`;
    await fs.writeFile(path.join(cache, filename), bytes);
    meta.preview = path.join(cache, filename);
    meta.previewSHA256 = sha(bytes);
    meta.previewReused = false;
  } else {
    const earlier = previous.sheets.find(s => s.name === spec.name);
    meta.preview = earlier.preview;
    meta.previewSHA256 = earlier.previewSHA256;
    if (sha(await fs.readFile(meta.preview)) !== meta.previewSHA256) throw new Error(`Preview changed ${spec.name}`);
    meta.previewReused = true;
  }
  meta.artifactValuesExact = true;
  console.log(JSON.stringify({ sheet: spec.name, rows: spec.rows.length, columns: spec.columns.length, preview: path.basename(meta.preview), reused: meta.previewReused }));
}
const errors = await workbook.inspect({ kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options: { useRegex: true, maxResults: 300 }, summary: 'final spreadsheet error scan', maxChars: 5000 });
manifest.errorScan = errors.ndjson;
await fs.writeFile(path.join(qa, 'workbook_inspections.json'), JSON.stringify(inspections, null, 2));
const exported = await SpreadsheetFile.exportXlsx(workbook);
await exported.save(out);
try {
  await fs.rename(`${out}.inspect.ndjson`, path.join(cache, 'workbook_export_inspect.ndjson'));
} catch (error) {
  if (error.code !== 'ENOENT') throw error;
}
manifest.inputSHA256 = sha(await fs.readFile(input));
manifest.outputSHA256 = sha(await fs.readFile(out));
manifest.status = 'EXPORTED_PENDING_INDEPENDENT_AND_VISUAL_QA';
await fs.writeFile(path.join(qa, 'workbook_build_manifest.json'), JSON.stringify(manifest, null, 2));
console.log(JSON.stringify({ status: manifest.status, sheets: manifest.sheets.length, path: out, sha256: manifest.outputSHA256 }));
