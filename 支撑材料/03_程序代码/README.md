# A题《药材的烘干问题》程序代码

本目录是可独立复制到其他位置的 CPU 计算工程。必需输入、四份原始结果模板、核心源码、固定版本依赖和冻结采样基准均在本目录内。所有输入路径以程序文件所在目录为根，不需要原作者电脑的盘符或上级工作区。

## 先运行哪一个命令

使用 64 位 Python。已测试环境为 Windows AMD64、Python 3.14.7、NumPy 2.5.2、SciPy 1.18.1、openpyxl 3.1.5。`diskDense.py` 使用此 SciPy 版本的 BDF 内部接口，先按 `requirements.txt` 安装指定版本。

在本目录打开终端，首次准备环境：

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip check
```

Linux/macOS 的虚拟环境解释器位置是 `.venv/bin/python`。这些系统未实际验证；上面的 Windows 环境已做同机隔离目录测试，具体范围见 `docs/运行验收说明.md`。

1. 检查文件是否齐全、哈希是否一致及模板能否打开：

   ```powershell
   .venv\Scripts\python.exe -X utf8 -B runDelivery.py --preflight-only
   ```

2. 运行 N40 小网格的三条轨迹和四题完整导出、回读：

   ```powershell
   .venv\Scripts\python.exe -X utf8 -B runDelivery.py --profile quick
   ```

3. 重算论文正式网格并核验冻结采样：

   ```powershell
   .venv\Scripts\python.exe -X utf8 -B runDelivery.py --profile final
   ```

`quick` 采用三条原物理模型、N=40；Q2 仍导出每秒完整日程，因此导出/回读会花数分钟。没有改成加速扩散参数或缩短烘干过程。N40只用于验证运行链条，不能替代正式结果。

`final` 为 Q1 N=3200、Q23 N=3200、Q4 N=6400，与冻结 `final_v6a` 参数一致。Q2/Q3共享同一次 Q23 求解。本包此次隔离环境全量实跑989.547秒（约16.5分钟），机器负载会影响实际耗时。Q4磁盘稠密多项式约8.33 GB，建议留足20 GB可用磁盘空间；已使用约32 GB内存电脑，未测定最低内存。各轨迹按顺序执行，BLAS/OMP线程固定为1，不需要GPU。

Windows也可用 `./runLogged.ps1 -Python .venv\Scripts\python.exe -Profile final`，在Python结束后额外写 `processExit.json` 留存实际退出码。该辅助脚本经过PowerShell静态解析；本轮真实隔离运行由外部Python监督器记录进程退出，不冒称此PowerShell封装已完成全量实跑。

每次自动生成新的 `results/<profile>_<UTC时间>/`，也可加 `--run-id my_final_01`。已有同名运行目录会被拒绝，不覆盖结果。主入口可从其他当前目录调用；程序自身以本目录为根。

## 文件对应关系

| 文件或目录 | 内容与用途 |
|---|---|
| `runDelivery.py` | 新的独立入口；输入预检、三轨迹调度、四表导出回读、数值对照及异常留痕 |
| `q1Model.py`、`q2Model.py`、`q4Model.py` | 三组问题参数与正式网格设置 |
| `q3Model.py` | 从Q23轨迹定位全域最大含水率事件和严格报告时刻 |
| `dryingCore.py` | 材料坐标圆柱控制体、物性、Kirchhoff水通量、BDF求解和诊断 |
| `analyticJacobian.py` | 解析稀疏Jacobian及可选小型数值差分自检 |
| `diskDense.py` | 原精度BDF多项式磁盘缓存与清理 |
| `numerical_design.md` | 与核心实现对应的控制体方程、势函数、守恒关系及事件定义 |
| `exportOutputs.py` | 四题原模板对应工作簿、原精度CSV、正文表及完整回读 |
| `inputs/original` | 题目附件1/2原始Excel，保留原字节 |
| `inputs/cleaned` | 经审计的环境241行和半径145行CSV，直接供求解器读取 |
| `inputs/templates` | 题目提供的四份原始结果模板，不是已计算结果 |
| `reference` | 冻结版本三份采样NPZ及精简数值摘要；仅作对照，不参与求解 |
| `input_manifest.json` | 输入、模板与基准SHA256；运行前逐项检查 |
| `docs/source_changes.json` | 原源码/副本SHA256、路径替换清单和算法AST核对 |
| `docs/portable_paths.diff` | 八核心模块的逐行可审查差异 |
| `A_CodeReview.sln`、`A_CodeReview.pyproj` | Visual Studio Python项目，需用户选择本机虚拟环境 |

历史实验、数据审计和交叉验证源码在支撑材料的 `07_数值检验与实验/历史源码`。它们保留历史输入路径，属于审查资料；其使用前提见该目录说明。当前正式复现入口是本目录的 `runDelivery.py`。

## 输出和判定

每个运行目录包含 `runResult.json`、`stdout.log`、三轨迹的 `summary.json` 和 `sampled_solution.npz`。`outputs/`包含 `result1.xlsx` 至 `result4.xlsx`、对应 `*.export.json`/`*.validation.json`、四份 `*_unrounded.csv.gz` 及七份正文CSV。原精度归档由 live Run 查询得到，不用60秒采样NPZ插值冒充每秒数据。运行产生的大表和可重建缓存不预先放入此代码包；已冻结四表在支撑材料 `04_结果表格`。

四份工作簿均逐格回读对照原精度归档，并独立抽查live Run；全部正文表从live Run逐格核验。模型本身检查求解成功、接受状态含水率/物性范围和干基质量残差≤1e-6。Q3/Q4另核验报告格点上未舍入的 `max(C)<0.15`。

正式复现的采样绝对容差已在运行前写入入口：温度5e-6 K、含水率/均值/累计失水5e-7、半径1e-10 m、连续事件0.005 s；严格报告时刻必须与冻结版本处在同一0.0001 h格点，且实际未舍入场严格达标。程序另记录全部已保存NPZ数组是否逐值完全相同。容差用于数值复现，不是物理模型准确率。冻结107项历史工程的整体验证不再是新包运行前提，也不会被标记为已经执行。

正确退出须同时满足终端退出码0和对应 `runResult.json.status=PASS`。只有输入预检时，PASS仅表示输入检查完成。程序不会代填 Visual Studio GUI复现或人工审查通过。

## 模型口径

内部单位是秒、米、开尔文和干基含水率。附件1只有0–4 h环境观测；4 h之后50°C/0.05是平台延拓假设。气相水分指标等同于材料边界平衡含水率、有效显热容量、径向同比收缩等仍为声明的模型闭合。Q4采用整组附录4物性并从t=0求解；固定2 cm列在材料域外留空，真实表面单列。连续 `max(C)=0.15` 与严格达标报告时间不同，四位显示0.1500不等于未舍入值已经严格小于阈值。

## Visual Studio人工复现

打开本目录 `A_CodeReview.sln`；需要安装Visual Studio的Python开发支持，在“Python环境”中添加/选择本目录 `.venv`，确认启动文件为 `runDelivery.py`、命令行参数为 `--profile quick`。项目没有绑定作者的解释器、安装目录、`.vs`缓存或用户配置。

建议在 `runQuestion` 调用逐问 `solve`处、`dryingCore.RadialModel.rhs`、`q3Model.completion`放置断点。查看t=0时301.15 K/2.55、半径/物性/通量、事件与报告时间、域外空白和四表验证信息；随后按正式网格运行并记录源码哈希、断点变量与实际退出。新版项目的GUI打开/运行尚未实测，代码人工签核状态仍为待用户审查。旧原工程曾有GUI记录，它只属于原工程版本。

可选Jacobian自检命令：`.venv\Scripts\python.exe -X utf8 -B analyticJacobian.py --self-test`。这也是独立小型实现检验，不能替代正式网格运行。
