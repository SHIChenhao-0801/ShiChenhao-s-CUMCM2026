# 比赛代码的 Visual Studio 人工审查与可视化复现

适用范围：仅 `D:\Document\数学建模`。用户要求记录于 2026-09-09；团队为福州大学参赛小组。

## 必须保留的分工

比赛中运行的 `.py`、`.cpp` 代码纳入可视化复现清单，主代理通过 Computer Use 在 Visual Studio 打开、展示并运行，核心代码由用户人工审查。CLI 批量计算可提供效率，但不能替代要求的 VS 图形界面复现。未发生的人工审查必须标记“待用户审查”。

## 每次交付的具体做法

1. 固定代码版本或 SHA-256、输入数据、配置、随机种子、依赖和结果目录。使用生成真实论文数据的同一份源文件，避免维护另一份演示代码。
2. 在 Visual Studio 打开对应解决方案、项目或源码；Python 确认解释器和工作目录，C++ 确认编译器、配置、架构和程序参数。大型依赖不能仅凭 VS 存在就假定可用。
3. 先展示整体入口，再定位数据读取/清洗、模型公式、目标函数、约束、求解步骤与结果输出。代码注释说明这些位置与论文公式、变量、单位的对应关系。
4. 对主要入口设置断点，使用 IDE 的启动/调试/单步按钮，查看局部变量、监视值、调用堆栈与输出；通过这些界面说明关键数组维度、参数、约束检查和结果含义。
5. 对照冻结结果与本次执行产物。数值差异超出容差时先解释或修复，不将“窗口打开”或“编译成功”登记为完整复现。
6. 保存审查清单、源码版本、运行记录和有必要的 UI 证据；用户确认后才登记“人工审查通过”。源代码、数据或模型变化后刷新对应复现与审查状态。

Computer Use 只操作编辑器、调试器等受支持界面，不在 Windows 终端或 IDE 集成终端中通过 UI 输入系统命令。需要构建或批量执行的命令使用正式执行工具；随后仍完成用户要求的 IDE 展示和调试。

## 推荐的审查记录字段

`question / entry_file / source_hash / environment / data_and_config / ide_project / breakpoints / command_or_launch_settings / outputs / numerical_checks / gui_reproduced / human_review_status / reviewer_notes`

正式赛题尚未指定时不虚构某问的审查通过记录。可将已有代码的清单放在 `paper_output/code-review/`；最终结果引用 `paper_output/results/` 中的真实证据。

## 2026-09-10 最新核实情况

Community 2026 已更新为 18.10.0（18.10.12201.205），安装完整且可启动。用户已明确允许继续 Computer Use。本轮实际打开两份解决方案，Python 3.14.7 在第 41 行断点、单步至第 42 行，C++ 在第 48 行断点、单步至第 50 行；查看回归系数和 RMSE 后继续运行，均输出通过。截图、源码版本、实际结果见 [09-10 验收单](2026-09-10-verification-and-acceptance.md)。人工审查仍为待用户确认，软件运行通过不等于本人已审查。

## 2026-09-09 历史核实情况

- IDE 文件存在：`D:\VisualStudio\Common7\IDE\devenv.exe`。
- Visual Studio Community 2026 18.9.3 注册信息：`isComplete=false`、`isLaunchable=false`、曾取消安装；C++ 和 Python 组件匹配只说明安装元数据。
- 使用 Computer Use 启动后未出现可操作的 VS 窗口，未完成任何 Python/C++ 的 VS GUI 复现。具体缺失或失败原因尚未定位，不能仅凭安装标记推断。
- Build Tools 2026 另有完整安装；它提供构建工具，不代表完整 IDE 已能使用。
- VS Code 1.136.1 另有安装；用户指定的是 Visual Studio，两者不作无声替代。
- 用户在本轮按 Esc 停止 Computer Use；其后未继续桌面操作。

上述历史缺项已在 09-10 的小型 Python/C++ GUI 验证中补齐。安装及环境可用性核实仍不等于正式赛题复现完成。
