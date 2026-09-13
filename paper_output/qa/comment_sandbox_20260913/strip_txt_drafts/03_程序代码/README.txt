A题《药材的烘干问题》程序运行说明

1. 本目录内容

本目录包含完整的CPU求解入口、八个核心模块、必需输入、原始结果模板和数值参照。读取路径以runDelivery.py所在目录为根，无须原作者电脑的盘符或上级工作区。

本次交付中没有JSON或Markdown文件。文件完整性清单为input_manifest.csv，冻结数值参照为reference/reference_data.py中的纯数据常量。八个核心模块的模型、数值方法、参数和四题导出规则保持不变。本轮已删除源码注释和Python说明性docstring，并完成非注释AST核对。

2. 安装与运行

使用64位Python。已经实际使用的环境是Windows AMD64、Python 3.14.7、NumPy 2.5.2、SciPy 1.18.1、openpyxl 3.1.5。diskDense.py依赖该SciPy版本的BDF内部接口，应按requirements.txt安装指定版本。

在本目录打开终端，首次执行：
  python -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  .venv\Scripts\python.exe -m pip check

输入和模板预检：
  .venv\Scripts\python.exe -X utf8 -B runDelivery.py --preflight-only

N40小网格三轨迹、四题完整导出及回读：
  .venv\Scripts\python.exe -X utf8 -B runDelivery.py --profile quick

正式N3200/N3200/N6400网格重算及冻结参照对照：
  .venv\Scripts\python.exe -X utf8 -B runDelivery.py --profile final

Windows可用辅助入口留存实际进程退出码：
  ./runLogged.ps1 -Python .venv\Scripts\python.exe -Profile final

每次自动生成不同运行目录；也可追加--run-id my_run_01指定编号。已有同名目录会被拒绝，不覆盖结果。Linux/macOS解释器通常为.venv/bin/python；这些系统尚未实际验证。

3. 文件作用

runDelivery.py：输入预检、三条轨迹调度、四表回读、数值对照和运行日志。
q1Model.py、q2Model.py、q4Model.py：各问题物性和求解设置；Q2/Q3共用Q23轨迹。
q3Model.py：连续事件及0.0001 h格点上的严格达标时刻。
dryingCore.py：材料坐标控制体、物性、Kirchhoff水通量、BDF和诊断。
analyticJacobian.py：解析稀疏Jacobian及可选数值差分自检。
diskDense.py：原精度BDF多项式磁盘缓存。
exportOutputs.py：原模板对应工作簿、原精度归档、正文表和完整回读。
numerical_design.txt：与源码对应的离散方程、守恒关系和事件定义。
inputs/original：附件1、附件2原始Excel。
inputs/cleaned：241行环境观测和145行半径观测CSV。
inputs/templates：四份原始结果模板，不是已计算结果。
reference：三份冻结采样NPZ及reference_data.py纯数据参照。
input_manifest.csv：上述输入、模板与参照的相对路径、字节数和SHA256。
docs/源码变更说明.txt：当前去注释规则、输入清单同步及源码前后SHA256。
docs/运行验收说明.txt：当前源码版本、静态检查和按版本区分的实际运行记录。
A_CodeReview.sln、A_CodeReview.pyproj：Visual Studio Python工程。

支撑材料中的05_数值检验与实验保存其余数值检验与实验源代码；这些历史入口的原路径依赖应按该目录说明处理。正式四份冻结大表在04_结果表格。

4. 运行产物和资源

运行结果保存在本目录results的独立子目录。包含四份Excel、对应原精度CSV.GZ、七份正文CSV、轨迹NPZ、stdout.log及程序校验记录。

为维持原有导出和回读校验协议，程序执行后仍会新生成JSON格式的运行记录、导出清单和验证记录；这些是运行产物，不是本次交付中遗留的JSON文件。重新整理或提交文件夹时，请区别随程序交付的源码/输入与本机运行生成的results目录。没有将原JSON内容改后缀冒充TXT说明。

Q2按每秒完整导出，所以N40也需要数分钟。此前N40三轨迹全流程实跑约454.516秒；此前正式网格全流程实跑约989.547秒。Q4稠密缓存约8.33 GB，建议留足20 GB磁盘空间；已使用约32 GB内存电脑，未测定最低内存。程序顺序运行三轨迹并固定CPU计算线程为1，不需要GPU。缓存会在轨迹完成、导出和回读后正常清理。

5. 数值口径和验收

内部单位为秒、米、开尔文和干基含水率。附件1只有0至4 h观测，后续50°C/0.05平台是延拓假设。气相指标映射到材料边界平衡含水率、有效显热容量和同比收缩仍是声明的模型闭合，数值自洽不等于实测准确率。

Q4固定半径列落在材料域外时留空，真实表面单列。连续max(C)=0.15与严格报告时间不同；程序在0.0001 h格点上查询未舍入全域最大值，必须严格小于0.15。

正式采样对照使用既定绝对容差：温度5e-6 K，含水率/均值/累计失水5e-7，半径1e-10 m，连续事件0.005 s；严格报告时间须保持同一0.0001 h格点。另记录保存数组是否逐值相同。四份工作簿完整回读对照原精度归档，并核对live Run；全部正文CSV从live Run逐格验证。

完成须同时检查进程退出码0和对应运行记录的PASS。仅输入预检时，PASS只表示预检完成。N40不能替代正式细网格的结果。

6. Visual Studio与人工审查

打开A_CodeReview.sln，需要Visual Studio的Python开发支持。选择本目录.venv解释器，启动文件为runDelivery.py，参数为--profile quick；工程没有绑定作者机器安装路径。

建议在runQuestion调用solve、RadialModel.rhs和q3Model.completion处设断点，观察初值301.15 K/2.55、物性和通量、事件与严格报告时间以及域外空白。新版工程的GUI打开、断点和运行尚未在本轮实测，用户人工审查仍待本人完成。CLI或静态检查不会代填GUI/人工审查通过。
