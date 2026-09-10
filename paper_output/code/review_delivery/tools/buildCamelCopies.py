"""只在本审查副本目录生成可追溯的驼峰命名版本；不运行生产求解。"""
from __future__ import annotations

import ast
import copy
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import tokenize

deliveryDir = Path(__file__).resolve().parents[1]
projectRoot = deliveryDir.parents[2]
sourceDir = projectRoot / 'paper_output/code/modeling'
moduleMap = {
    'drying_core': 'dryingCore', 'analytic_jacobian': 'analyticJacobian',
    'disk_dense': 'diskDense', 'q1_model': 'q1Model', 'q2_model': 'q2Model',
    'q3_model': 'q3Model', 'q4_model': 'q4Model', 'export_outputs': 'exportOutputs',
}
protectedNames = {
    # 外部 BDF 注入参数、SciPy 子类协议及其原生属性名必须保留。
    'dense_cache', 't_shift', 't_old', '_call_impl', '_dense_output_impl',
}
explicitMap = {
    '_sha': 'sha256File', '_record': 'exportFileRecord', '_json': 'writeJson',
    '_qid': 'normalizeQuestionId', '_q4': 'roundFourDecimals',
    '_template': 'loadTemplate', '_sheet': 'createSheet',
    '_sparsity': 'buildSparsity',
    '_manifest_path': 'resolveManifestPath', 'constant_d': 'constantDiffusivity',
}
pathMap = {
    'paper_output/code/modeling/drying_core.py': 'paper_output/code/review_delivery/dryingCore.py',
    'paper_output/code/modeling/export_outputs.py': 'paper_output/code/review_delivery/exportOutputs.py',
    'paper_output/results/export_selfcheck': 'paper_output/code/review_delivery/runtime/exportSelfcheck',
    'results/jacobian_validation': 'code/review_delivery/runtime/jacobianValidation',
}
# 元数据既可能用完整路径，也可能用 SOURCE.with_name('q3_model.py')；两者均登记。
for oldModule, newModule in moduleMap.items():
    pathMap[oldModule + '.py'] = newModule + '.py'
    pathMap['paper_output/code/modeling/' + oldModule + '.py'] = 'paper_output/code/review_delivery/' + newModule + '.py'


def toCamel(name):
    if name == '_' or name.startswith('__') or name.isupper() or name in protectedNames:
        return name
    if name in explicitMap:
        return explicitMap[name]
    parts = name.lstrip('_').split('_')
    return parts[0] + ''.join(part[:1].upper() + part[1:] for part in parts[1:])


sourceTrees = {}
sourceTexts = {}
renameMap = dict(moduleMap)
importedNames = set()
bindingNames = set()
callableNames = set()
for oldModule in moduleMap:
    sourceText = (sourceDir / (oldModule + '.py')).read_text(encoding='utf-8-sig')
    sourceTexts[oldModule] = sourceText
    sourceTrees[oldModule] = ast.parse(sourceText)
    for node in ast.walk(sourceTrees[oldModule]):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bindingNames.add(node.name)
            callableNames.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            bindingNames.add(node.id)
        elif isinstance(node, ast.arg):
            bindingNames.add(node.arg)
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
            if isinstance(node.value, ast.Name) and node.value.id == 'self':
                bindingNames.add(node.attr)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            isLocal = isinstance(node, ast.ImportFrom) and node.module in moduleMap
            for alias in node.names:
                if not isLocal and alias.name not in moduleMap:
                    importedNames.add(alias.asname or alias.name.split('.')[0])
for name in sorted(bindingNames):
    if name not in importedNames and toCamel(name) != name:
        renameMap[name] = toCamel(name)
if len(set(renameMap.values())) != len(renameMap):
    conflicts = {value: [key for key, mapped in renameMap.items() if mapped == value] for value in renameMap.values() if list(renameMap.values()).count(value) > 1}
    raise RuntimeError('重命名映射存在冲突，停止生成：' + repr(conflicts))
for originalName, newName in renameMap.items():
    if newName in bindingNames and newName != originalName:
        raise RuntimeError(f'已有同名绑定，停止生成：{originalName} -> {newName}')


class RenameTree(ast.NodeTransformer):
    """仅改自有标识符；外部调用关键字与文件数据 schema 不改。"""
    def visit_Name(self, node):
        node.id = renameMap.get(node.id, node.id)
        return node

    def visit_arg(self, node):
        node.arg = renameMap.get(node.arg, node.arg)
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        node.name = renameMap.get(node.name, node.name)
        return self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Attribute(self, node):
        # argparse 的 Namespace 字段由原命令行开关生成，保留这个外部协议。
        isArgparse = isinstance(node.value, ast.Name) and node.value.id in ('args', 'arguments')
        if not isArgparse:
            node.attr = renameMap.get(node.attr, node.attr)
        return self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            alias.name = moduleMap.get(alias.name, alias.name)
            if alias.asname:
                alias.asname = renameMap.get(alias.asname, alias.asname)
        return node

    def visit_ImportFrom(self, node):
        if node.module in moduleMap:
            node.module = moduleMap[node.module]
            for alias in node.names:
                alias.name = renameMap.get(alias.name, alias.name)
                if alias.asname:
                    alias.asname = renameMap.get(alias.asname, alias.asname)
        return node

    def visit_Call(self, node):
        functionName = node.func.id if isinstance(node.func, ast.Name) else (
            node.func.attr if isinstance(node.func, ast.Attribute) else None)
        isSettingsUpdate = isinstance(node.func, ast.Attribute) and node.func.attr == 'update' and (
            isinstance(node.func.value, ast.Name) and node.func.value.id == 'settings')
        if functionName in callableNames or isSettingsUpdate:
            for keyword in node.keywords:
                keyword.arg = renameMap.get(keyword.arg, keyword.arg)
        if functionName == 'getattr' and len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
            key = node.args[1].value
            if key == 'input_records':
                node.args[1].value = renameMap[key]
        return self.generic_visit(node)

    def visit_Assign(self, node):
        # 这是 Settings 构造参数，不是已冻结的输出 schema。
        isSettings = any(isinstance(target, ast.Name) and target.id == 'settings' for target in node.targets)
        if isSettings and isinstance(node.value, ast.Dict):
            for key in node.value.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    key.value = renameMap.get(key.value, key.value)
        return self.generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            node.value = pathMap.get(node.value, node.value)
        return node


commentRules = {
    'dryingCore': [
        ('def loadInputs(', '# 原始环境时间单位为秒，温度为 K，含水率为 kg 水 / kg 干物质；记录输入哈希。'),
        ('class Settings:', '# 数值参数集中配置；四问正式设置由 q1Model/q2Model/q4Model 提供。'),
        ('        self.x = np.linspace', '        # x=r/R(t) 是无量纲材料坐标；控制体权重来自圆柱半径方向的积分。'),
        ('    def environment(', '    # 4 h 之后采用已声明的平台延拓；不能把外推段称为实测环境。'),
        ('    def properties(', '    # rho*cp 为有效显热体积容量；干物质量通过独立的积分守恒式约束。'),
        ('        positiveC = np.maximum', '        # 仅延拓 Newton 试探点的系数；不裁剪被接受的温度或含水率状态。'),
        ('    def waterInternalFlux(', '    # Kirchhoff 势差积分处理强非线性 D(C)，温度因子在同一面上取值。'),
        ('        potential = ', '        # 势 F(C)=C*exp(-a/C)+a*Ei(-a/C)，导数为 exp(-a/C)。'),
        ('        thermalFactor = ', '        # 不能对温度因子乘势后的整体作差，否则会引入题设没有的交叉扩散通量。'),
        ('    def rhs(', '    # 状态交错排列 T0,C0,T1,C1,...，最后一项累计平均失水；共享面通量保证离散守恒。'),
        ('        waterG[-1] = ', '        # 表面对流传质和传热采用外法向流出约定；中心面面积为零。'),
        ('        derivative[:-1:2] = ', '        # 除以 R(t)^2 与控制体权重得到材料导数；同比收缩无需额外网格对流项。'),
        ('    def fields(', '    # materialX 查询材料坐标；radiiM 查询实际米制半径，收缩域外返回 NaN。'),
        ('    def diagnostics(', '    # 每块至多 256 个被接受时刻，避免对高网格状态和物性数组再做整域复制。'),
        ('    def dryEvent(', '    # 连续事件取整个离散材料域 max(C)=0.15；严格达标还须在事件后重新检查。'),
        ('            end = float(np.ceil', '            # 从实际事件状态继续积分至 ceil(event)+1 秒，不依赖外推或四位舍入。'),
        ('def saveRun(', '# 保存 60 s 等审查采样、源码/输入哈希和状态；整秒题表由 exportOutputs 直接查询 live Run。'),
    ],
    'analyticJacobian': [
        ('def harmonicPartials(', '# 调和平均面对左右节点的解析偏导，供热通量与调和水通量使用。'),
        ('def jacobian(', '# 稀疏 Jacobian 按交错 T/C 状态组装；保留物性、水通量与容量分母的全部链式法则项。'),
        ('    heatDeriv = ', '    # 每个面的四列依次为 T左、C左、T右、C右，对相邻两个控制体施加相反符号。'),
        ('        if np.any(small):', '        # 近等浓度时对实际 RHS 使用的中点分支求导，避免与求解器分支不一致。'),
        ('    values.append(-tempDerivative', '    # 热容量随 C 改变，必须保留 -Tdot*(容量对C偏导)/容量 这一局部项。'),
        ('    matrix = coo_matrix', '    # 面模板只有邻近耦合；COO 合并重复贡献后转 CSC，交给 BDF 稀疏线性求解。'),
        ('def selfTest(', '# 此历史自检入口仅验证导数和小网格接线，不能替代正式网格与人工代码审核。'),
    ],
    'diskDense': [
        ('class DenseCache:', '# 每个 Run 独享项目内可重建缓存；存原始 float64 字节，不降低插值阶数。'),
        ('    def storeAccepted(', '    # 被接受的整段状态写为磁盘映射数组，以限制长时高网格运行的常驻内存。'),
        ('    def close(', '    # 先释放 Windows 文件映射，再仅清理当前对象创建并验证过的私有缓存。'),
        ('    def _call_impl(', '    # 保留 SciPy override 名，调用安装版本的原生 BDF 多项式求值器。'),
        ('class DiskBDF(', '# dense_cache 是 solve_ivp 注入此子类的协议参数，保留拼写以维持接口。'),
        ('def alignBdfSegments(', '# 子类不命中 SciPy 对 BDF 的类身份判断，故恢复其接受断点右侧多项式选择。'),
    ],
    'q1Model': [('def solve(', '# Q1 全部 1800 秒均采用附录 2 参数，正式空间区间数默认 3200。')],
    'q2Model': [('def solve(', '# Q2/Q3 从 t=0 采用附录 3，Q3 必须复用本次同一个 Run，不能拼接 Q1。')],
    'q3Model': [
        ('def completion(', '# Q3 是 Q2 场解的阈值泛函；先连续定位，再向上取 0.0001 h 并验原精度 max(C)<0.15。'),
        ('    while True:', '    # 即使四位显示为 0.1500，也只能依据未舍入含水率判定严格干燥。')],
    'q4Model': [('def solve(', '# Q4 从 t=0 使用整组附录 4 系数，并按观测 R(t) 同比径向收缩，固定长度。')],
    'exportOutputs': [
        ('def fieldBlock(', '# 固定 21 个物理半径逐块查询，Q4 域外保持空白；实际表面单独用 x=1 查询。'),
        ('def exportQuestion(', '# 逐秒数据直接求值于 live Run 的 BDF 密集解；不从 60 s NPZ 再插值生成。'),
        ('def validateExports(', '# 回读 XLSX/原精度压缩 CSV 并与同一个 live Run 独立查询比对。'),
        ('def paperTables(', '# 正文表独立生成，单位和显示位数跟随题目模板，原精度数值另存。'),
        ('def createSheet(', '# 按官方表头设置工作簿；write_only 流式输出降低大题表的内存峰值。'),
    ],
}


def addComments(text, newModule):
    lines = text.splitlines()
    rules = commentRules[newModule]
    result = ['# 本文件为冻结求解源码的驼峰审查副本；来源、改名与 AST 核验见 tools/coreRenameReport.json。']
    for line in lines:
        for prefix, comment in rules:
            if line.startswith(prefix):
                result.append(comment)
        result.append(line)
    return '\n'.join(result) + '\n'


class NormalizeTree(ast.NodeTransformer):
    """独立反向规范化：只允许登记的名字/路径/构造参数键变化。"""
    def __init__(self):
        self.reverseNames = {value: key for key, value in renameMap.items()}
        self.reversePaths = {value: key for key, value in pathMap.items()}

    def generic_visit(self, node):
        for field, value in ast.iter_fields(node):
            if field in ('id', 'arg', 'attr', 'name', 'asname', 'module') and isinstance(value, str):
                setattr(node, field, self.reverseNames.get(value, value))
        return super().generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            node.value = self.reversePaths.get(node.value, node.value)
        return node

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'getattr':
            if len(node.args) > 1 and isinstance(node.args[1], ast.Constant) and node.args[1].value == 'inputRecords':
                node.args[1].value = 'input_records'
        return self.generic_visit(node)

    def visit_Assign(self, node):
        if any(isinstance(target, ast.Name) and target.id == 'settings' for target in node.targets) and isinstance(node.value, ast.Dict):
            for key in node.value.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    key.value = self.reverseNames.get(key.value, key.value)
        return self.generic_visit(node)


def preserveFormatting(oldModule, transformed):
    sourceText = sourceTexts[oldModule]
    sourceLines = sourceText.splitlines(keepends=True)
    lineOffsets = [0]
    for line in sourceLines:
        lineOffsets.append(lineOffsets[-1] + len(line))

    def index(position):
        return lineOffsets[position[0] - 1] + position[1]

    # Python AST 列号为 UTF-8 字节偏移，tokenize 列号为 Unicode 字符偏移。
    def astPosition(row, byteColumn):
        column = len(sourceLines[row - 1].encode('utf-8')[:byteColumn].decode('utf-8'))
        return row, column

    protectedPositions = set()
    replacements = []
    for before, after in zip(ast.walk(sourceTrees[oldModule]), ast.walk(transformed)):
        if type(before) is not type(after):
            raise RuntimeError('标识符转换意外改变 AST 结构')
        if isinstance(before, ast.keyword) and before.arg in renameMap and before.arg == after.arg:
            protectedPositions.add(astPosition(before.lineno, before.col_offset))
        elif isinstance(before, ast.Attribute) and before.attr in renameMap and before.attr == after.attr:
            end = astPosition(before.end_lineno, before.end_col_offset)
            protectedPositions.add((end[0], end[1] - len(before.attr)))
        elif isinstance(before, ast.Constant) and before.value != after.value:
            replacements.append((index(astPosition(before.lineno, before.col_offset)),
                                 index(astPosition(before.end_lineno, before.end_col_offset)), repr(after.value)))
    for token in tokenize.generate_tokens(io.StringIO(sourceText).readline):
        if token.type == tokenize.NAME and token.string in renameMap and token.start not in protectedPositions:
            replacements.append((index(token.start), index(token.end), renameMap[token.string]))
    for start, end, value in sorted(replacements, reverse=True):
        sourceText = sourceText[:start] + value + sourceText[end:]
    return sourceText


records = []
for oldModule, newModule in moduleMap.items():
    transformed = RenameTree().visit(copy.deepcopy(sourceTrees[oldModule]))
    ast.fix_missing_locations(transformed)
    targetText = addComments(preserveFormatting(oldModule, transformed), newModule)
    targetTree = ast.parse(targetText)
    normalized = NormalizeTree().visit(copy.deepcopy(targetTree))
    originalDump = ast.dump(sourceTrees[oldModule], include_attributes=False)
    normalizedDump = ast.dump(normalized, include_attributes=False)
    if originalDump != normalizedDump:
        import difflib
        difference = '\n'.join(difflib.unified_diff(originalDump.split(', '), normalizedDump.split(', ')))
        raise RuntimeError(f'{newModule}: 反向归一化 AST 不一致\n{difference[:8000]}')
    targetPath = deliveryDir / (newModule + '.py')
    # 未变化模块不重写，防止正在复核的其他副本被无意义触碰。
    if not targetPath.exists() or targetPath.read_text(encoding='utf-8') != targetText:
        targetPath.write_text(targetText, encoding='utf-8', newline='\n')
    originalPath = sourceDir / (oldModule + '.py')
    records.append({
        'originalPath': originalPath.relative_to(projectRoot).as_posix(),
        'originalSha256': hashlib.sha256(originalPath.read_bytes()).hexdigest(),
        'reviewPath': targetPath.relative_to(projectRoot).as_posix(),
        'reviewSha256': hashlib.sha256(targetPath.read_bytes()).hexdigest(),
        'normalizedAstSha256': hashlib.sha256(normalizedDump.encode('utf-8')).hexdigest(),
        'normalizedAstIdentical': True,
    })
report = {
    'status': 'PASS', 'createdUtc': datetime.now(timezone.utc).isoformat(),
    'scope': '8 review copies; reverse-normalized AST equality, no production solve in this script',
    'moduleMap': moduleMap, 'identifierMap': renameMap, 'pathMap': pathMap,
    'exceptions': sorted(protectedNames),
    'schemaPolicy': 'Explicit output dictionary/CSV/NPZ keys unchanged. Settings dataclass/asdict keys use new field names. Historical Settings(**settings) configuration keys renamed; argparse Namespace and third-party kwargs preserved.',
    'changes': ['Token-level identifier renaming and local import updates, preserving original layout', 'Registered provenance/selfcheck path updates', 'Chinese explanatory comments'],
    'files': records,
    'guiReproduced': False, 'humanReview': 'pending',
}
(deliveryDir / 'tools/coreRenameReport.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': 'PASS', 'modules': len(records), 'renamedIdentifiers': len(renameMap)}, ensure_ascii=False))
