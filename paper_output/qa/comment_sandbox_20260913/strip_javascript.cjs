const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { babelParse } = require('C:/Users/Shi Chenhao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/lib/transform/babelBundle.js');
const qa = __dirname;
const relative = '05_数值检验与实验/MATLAB对照证据/compareMatlab.mjs';
const source = path.join(qa, 'before', relative);
const candidate = path.join(qa, 'candidate', relative);
const original = fs.readFileSync(source, 'utf8');
const tree = babelParse(original, source, true);
let changed = original;
for (const comment of [...tree.comments].sort((a,b) => b.start-a.start)) {
  changed = changed.slice(0,comment.start) + changed.slice(comment.start,comment.end).replace(/[^\r\n]/g, ' ') + changed.slice(comment.end);
}
changed = changed.split(/\r?\n/).map(line => line.trimEnd()).join('\n').replace(/\n{4,}/g, '\n\n\n').replace(/^\n+/, '');
const newTree = babelParse(changed, candidate, true);
function normalized(node) {
  if (Array.isArray(node)) return node.map(normalized);
  if (!node || typeof node !== 'object') return node;
  const result = {};
  for (const [key,value] of Object.entries(node)) {
    if (['comments', 'leadingComments', 'trailingComments', 'innerComments', 'loc', 'start', 'end', 'extra', 'tokens'].includes(key)) continue;
    result[key] = normalized(value);
  }
  return result;
}
const beforeAst = JSON.stringify(normalized(tree));
const afterAst = JSON.stringify(normalized(newTree));
if (beforeAst !== afterAst) throw new Error('JavaScript AST changed beyond comments and positions');
if (newTree.comments.length) throw new Error('JavaScript comments remain');
fs.writeFileSync(candidate, changed, 'utf8');
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const report = {
  path: relative, language: 'JavaScript (ES module)', parser: 'Babel parser via bundled Playwright babelParse',
  comment_count: tree.comments.length, comments: tree.comments.map(c => ({type:c.type, line:c.loc.start.line, end_line:c.loc.end.line})),
  docstring_count: 0, remaining_comment_count: newTree.comments.length, ast_equal_without_comments: true,
  normalized_ast_sha256: hash(beforeAst), before_sha256: hash(Buffer.from(original)), after_sha256: hash(Buffer.from(changed)),
  before_bytes: Buffer.byteLength(original), after_bytes: Buffer.byteLength(changed), parser_check: 'PASS',
  runtime_check: 'PENDING_ROOT_SANDBOX'
};
fs.writeFileSync(path.join(qa, 'strip_javascript_audit.json'), JSON.stringify(report, null, 2)+'\n');
console.log(JSON.stringify(report));
