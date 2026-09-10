# A题正式生产发布契约：按当前守卫和证据审计实现核对

本文件是生产接口说明，不是模型结果。由workflow_contracts独立读取当前已启用Standard工作流脚本后整理；不修改core、主入口、guard、结果账本或图表索引，不在此填写未运行数值。

依据：`.agents/skills/model-code-and-result-generator/SKILL.md`；`paper-workflow-orchestrator/scripts/workflow_guard.py`的check_s4/check_s5/check_s6；`quality-assurance-auditor/scripts/evidence_gate.py`的provenance_failures、run_manifest_failures和evaluate。共享Skill按父目录只读复用。

## 1. 必须存在的文件与顶层类型

| 文件 | 顶层结构和必需条目 | 当前脚本实际检查 |
|---|---|---|
| `paper_output/code/modeling/run_modeling.py` | 实际统一运行入口 | S4检查存在；运行账本记录真正执行过的脚本 |
| `paper_output/code/modeling/q1_model.py`—`q4_model.py` | 按问组织的实际实现或实际被入口调用的薄封装 | S4仅检查至少一个`q*_model.py`存在；不据此省略四问实现 |
| `paper_output/results/model_results.json` | 对象，`questions`为逐问对象数组 | 正式审计根据model_route的Q1—Q4逐一检查，不得缺问 |
| `paper_output/results/metrics.json` | 对象，`items`为逐问指标对象数组 | 每問有有效value；不得无穷、NaN、null、空串 |
| `paper_output/results/conclusions.json` | 对象，`items`为逐问结论对象数组 | 每问至少一个非空`conclusion_text` |
| `paper_output/results/run_manifest.json` | 对象，`status="PASS"`，`runs`为真实运行数组 | 脚本哈希、输入/输出大小及哈希、returncode、输出关联与QID一致 |
| `paper_output/tables/table_index.json` | 对象，`tables`为表格对象数组 | `question_id`映射各问，文件真实存在且非空；可有ALL共享表，但不能替代逐问回答 |
| `paper_output/figure_index.json` | 对象，`figures`为图对象数组 | 所列已采用图必须真实存在；不能保留未生成路径当已完成 |
| `paper_output/plan/model_route.json` | 现有S2对象，`questions[].question_id`为Q1—Q4 | 正式证据审计的唯一问号集合来源 |
| `paper_output/qa/evidence_gate_report.json` | 由官方审计脚本实际运行生成 | S6要求PASS且其七个契约输入的当前哈希没有变化 |

所有新JSON建议统一含`schema_version: "1.0"`、`generated_by`（真实脚本路径）、`generated_at`（含时区的ISO时间）。路径在JSON中统一为相对本届根目录、使用`/`分隔；对用户文件链接使用绝对路径。

## 2. 文件记录与来源记录是两种不同类型

以下为类型说明，不是可以复制充当实际运行的JSON值。

```text
FileRecord := {
  path: string,          # 相对2026CUMCM，文件真实存在
  bytes: integer,       # 实际字节数>0
  sha256: string,       # 实际文件SHA256，小写十六进制
  exists: true
}

ExecutionProvenance := {
  source_code_path: string,
  source_code_sha256: string,
  run_command: string,
  run_exit_code: 0,      # 仅实际成功运行后写入
  output_artifacts: string[]  # 注意：这里必须是路径字符串列表
}
```

`execution_provenance.output_artifacts`必须是字符串列表。当前审计直接将每项传给`Path()`，不能把exporter返回的FileRecord对象原样放进去。相反，`run_manifest.runs[].output_artifacts`必须是FileRecord对象列表，审计从每项读取`path`、`exists`、`bytes`、`sha256`。

两者关联：每个provenance输出字符串必须出现在匹配run的FileRecord.path集合中；`source_code_path`归一化后必须与该run的`script`一致。其`source_code_sha256`和run的`script_sha256`均取真正被执行的同一脚本文件。

主入口直接完成四问时，可以记录一条`script=paper_output/code/modeling/run_modeling.py`、`question_ids=[Q1,Q2,Q3,Q4]`的成功run，四问结果均指向此主入口。若实际分进程执行q1—q4，则分别记录真实子进程脚本、命令、返回码，并让对应问的provenance匹配真实记录。不要声称执行过只被写出而从未调用的封装。

## 3. model_results最小建议

```text
{
  schema_version, generated_by, generated_at,
  questions: [
    {
      question_id: "Q1" | "Q2" | "Q3" | "Q4",
      status: "computed",
      model_name: string,
      result_summary: string,       # 从本次结果生成的非空文字
      execution_provenance: ExecutionProvenance,
      result_files: string[],       # 建议附加，可指向原始精度和导出
      assumptions_used: string[],
      limitations: string[],
      validation_summary: object
    }
  ]
}
```

`result_summary`应逐问回答：Q1指定时间空间的温湿变化；Q2全程耦合和前三小时表格；Q3全域阈值事件及严格验证时刻；Q4收缩和新物性下的同类结果。Q2和Q3复用同一物理Run，不能为满足四条记录无意义重复求解，亦不能分别使用不一致解。

Q3/Q4同时保存连续临界时刻event_s、用于严格低于阈值的post-verification end_s、未舍入最终max(C)。当前core使用ceil(event_s)+1，这是保守后验秒，不能称“已证明最早整数达标秒”。连续阈值点可显示0.1500，但四位小数不能用于严格阈值判断。

## 4. metrics与conclusions最小建议

```text
MetricItem := {
  question_id: string,
  metric_name: string,
  metric_role: string,
  value: number,               # 真实有限标量；JSON用allow_nan=False
  unit: string,
  status: "computed",
  evidence_path: string,
  interpretation: string
}

ConclusionItem := {
  question_id: string,
  conclusion_text: string,
  status: "computed",
  supporting_metrics: string[],
  supporting_artifacts: string[],
  assumptions: string[],
  limitations: string[]
}
```

建议每问至少保留实际守恒残差、所采用分辨率和至少一个直接回答题意的量。Q1可加入独立Bessel热误差、早期网格敏感性；Q2保留中心/表面三小时温湿值与耦合参数范围；Q3/Q4保留临界时长、后验max(C)、网格/时间步时长变化；Q4另有同附录4物性固定/收缩时长差。

无内部观测真值，不能填写“实测RMSE”“模型预测准确率”。采样网格对照的最大差不能称全连续域的严格误差上界；边界工况/潜热/端面情景差异不能称统计置信区间。REVIEW_REQUIRED等验证发现应保留在limitations/validation_summary，不通过改成computed掩盖未达到的精度目标；computed只表示实际算出。

当前审计对状态黑名单包括`missing`、`needs_real_modeling`、`draft_contract`、`to_be_filled`、`template`、`draft`、`scaffold_result_needs_review`。正确做法是只将实际完成证据列为computed，而不是选择不在黑名单的字符串绕开真实性要求。`evidence_status`若存在会优先于`status`，不能遗留相互冲突状态。

## 5. run_manifest最小建议及写入顺序

```text
{
  schema_version, generated_by, generated_at,
  status: "PASS",              # 仅全部所列必要步骤成功后
  runs: [
    {
      run_id: string,
      script: string,
      script_sha256: string,
      command: string,
      question_ids: string[],
      returncode: 0,
      cwd: string,
      started_at: string,
      finished_at: string,
      elapsed_seconds: number,
      python: {executable, implementation, version, platform},
      input_files: FileRecord[],
      output_artifacts: FileRecord[]
    }
  ]
}
```

`returncode`是当前审计读取的键，不能只有`exit_code`。每个output必须显式`exists:true`；缺此键会被当前审计当作缺失输出。建议记录依赖代码（drying_core.py、export_outputs.py、validate_bessel.py、绘图代码等）为input_files或单独受审计的依赖列表，使主入口未变但helper改变的情况仍被捕获。输入包括实际采用的清洗CSV、原输入、关键配置/模型路线以及验证记录；每项记录真实哈希。

推荐生产顺序：

1. 固定本次代码和配置版本并记录起始哈希，运行真实求解、独立验证及所采用情景。
2. 从持有的live Run生成所有完整输出、正文CSV、图和导出回读报告。生产过程中发现修改代码需要重新载入并重跑受影响部分。
3. 写model_results、metrics、conclusions、table_index、figure_index。这些都只指向已存在的leaf产物；不要让结果文件嵌入尚未生成的run_manifest哈希。
4. 再核对代码和输入没有变化，收集所有最终文件的大小与SHA256，最后写run_manifest。不要把run_manifest自己的哈希放入自己的output_artifacts，避免自引用哈希不可能闭合；不要把尚未运行的evidence_gate_report列为本次模型运行输出。
5. 实际运行S5检查和official evidence_gate；由脚本生成S6报告。之后不再改七份门禁输入。若图、模型路线、指标或索引有任何更新，重新执行相应真实生成步骤及门禁，不能手工续签报告哈希。

## 6. 表与图索引

```text
TableItem := {
  table_id: string,
  question_id: "Q1" | "Q2" | "Q3" | "Q4" | "ALL",
  title: string,
  purpose: string,
  path: string,
  status: "computed",
  placeholder: false,
  ok: true,
  exists: true,
  bytes: integer,
  sha256: string,
  source_run_id: string
}

FigureItem := {
  figure_id: string,
  question_id: string,
  title: string,
  purpose: string,
  path: string,
  status: "computed",
  placeholder: false,
  ok: true,
  exists: true,
  bytes: integer,
  sha256: string,
  source_run_id: string
}
```

外层分别为`{"tables":[...]}`、`{"figures":[...]}`并加通用元数据。`path`指向真实文件，不以expected_path代替未生成图。建议正文表固定归档`paper_output/tables/`；exporter生成在选定输出目录的正文CSV可由主入口复制到该正式表路径并同时登记原件/复制件哈希。图建议归档`paper_output/figures/`，图的数值来自本次冻结结果，检查标题、坐标、单位和图例。

当前正式审计对每問至少要求图或表之一，但用户任务和S2路线有更完整逐问图表与验证要求，不能利用最低检测覆盖不足省略。仅用于规划的未生成图继续留在visualization_plan或model_route，别混入现成figure_index的已采用图列表。已有真实数据图可以保留；它们不能取代所需结果图或结论。

## 7. exporter接口和实际自检范围

```python
from export_outputs import export_question, validate_exports

record = export_question(run, "Q2", output_dir)
check = validate_exports([record], runs={"Q2": run})
```

export_question返回workbook_path、manifest_path、artifacts、逐sheet行数/列数/首末时间/域外空值数和实际体积。artifacts为FileRecord风格对象；映射到ExecutionProvenance时只取path字符串，映射到run_manifest时保持对象并保证exists:true。

Q1/Q2两表采用温度°C和干基水分，首列时间s、第一行距离cm；逐秒完整时序由run.fields分块直接查询，不从60s NPZ补出。Q3/Q4采用每60s网格并额外加入连续临界事件和严格后验末时刻；原始浮点时间保存在archive和manifest，XLSX数值保存四位小数。极端情况下临界时刻的四位舍入可能与规则采样秒相同，manifest记录rounding_duplicate_time_count，原始时间仍可复核。

Q4固定0—2cm每0.1cm列加独立“药材表面”列；r>R(t)置None，不能置0；另有“半径”sheet给真实表面坐标。判断域内采用1e-12m的浮点边界容差。正文Q4每0.5cm列同样按时刻留域外空值，并附真实表面和半径CSV。最终MD/论文要说明表面列不等于2cm。

已用实际Q1 N40求解实施export自检：1801时间点×21径向位置，两张sheet均1802行（含表头）、22列。XLSX实际391199字节，未舍入17有效数字CSV.gz实际584943字节。全表流式回读、时间/半径/格式/有限数值核对、原始浮点归档逐行比对、独立重新调用live Run样本均通过，`fully_verified_with_live_Run=true`。这仅证明导出忠实性，不接受N40的物理精度；产物仅在`paper_output/results/export_selfcheck/`，不能覆盖正式result1。

保存后的两张Q1 worksheet已由Artifact Tool实际导入、渲染，已目视检查数字、标题及四位格式可读。PNG均生成可读；渲染Node进程在打印完成后返回1，因此只记录“实际图像已生成并检查”，不记录渲染命令整体PASS。正式四问结果仍应各自检查保存后显示。VS GUI复现与用户人工审查尚未由本导出任务完成。

## 8. Q2全程与20M体积

原题Q2先要求建立整个烘干过程模型，再要求正文列前三小时表格，随后要求每隔1s、0.1cm的“完整结果”。它未给result2单独终止时刻。当前S1/S2解释为从0到Q3的严格验证终点完整保存，并可提取前三小时；这一明确解释不能在发现文件大后静默改为3h。

exporter按完整时空网格实际写出并记录XLSX字节数，超过20,000,000字节会标记提示，不删除时刻、位置或数值。这个20MB阈值只是先采用保守的字节提醒；正式讲义的PDF和支撑zip/rar各20M限制仍需核验最终打包文件大小，不能只看单个xlsx。多个结果xlsx、代码、AI使用材料等合包后才是支撑大小。

未舍入CSV.gz是内部复核归档，默认不自动进入提交支撑包。它不能因为内部较大而删除；若团队决定提交它，同样要计入最终包。实际完整Q2导出前不按Q1体积线性外推声称合规。若最终完整包超限，应报告实际逐文件体积，再尝试无损压缩等不减少题定数据的处理；需要改变提交格式/范围时明确解决题意解释，不能伪装已经满足原要求。

## 9. 门禁通过的边界

当前S4检查主要是脚本文件存在，S5/S6主要是契约、来源、哈希、状态和文件存在性。它们不能自动证明方程物理正确、经验密度与骨架闭合合理、数值误差足够小、GUI已执行或用户已审查。独立物理推导、Bessel对照、非线性/收缩的守恒与网格时间步收敛、边界/端面/潜热情景及明示的验证局限必须保留为实质证据。原始数据、模型和公式变动后重新计算与复核，不能只让契约形式通过。
