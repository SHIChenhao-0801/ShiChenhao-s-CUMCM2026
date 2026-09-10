# 本次比赛 GitHub 备份

设置日期：2026-09-10（北京时间）。用户要求本次产生的代码和文件保存在 GitHub。

- 本地仓库：`D:\Document\数学建模\2026CUMCM`，仅覆盖本届正式比赛目录。
- 远端：<https://github.com/SHIChenhao-0801/ShiChenhao-s-CUMCM2026>，分支 `main`，远端名 `origin`。
- 设置时通过已登录的 GitHub API 核实为 **private**，当前账号有推送权限。登录继续使用本机 Git Credential Manager，不将令牌写入文件。
- 保留 GitHub 原有 Initial commit；在其基础上纳入本地文件。禁止使用强制推送或清理命令覆盖团队工作。
- `.gitattributes` 禁用自动换行转换，保留文件字节和已登记的来源/结果/提交哈希；文本仍可正常查看差异。
- 每完成一个可复核工作单元，检查新增/修改/删除文件、凭据和体积后提交并推送；即使模型或稿件尚未通过验证，也可备份，提交说明须保留真实状态。Git 备份不等于模型验证、论文冻结或用户人工审查通过。
- 已按用户后续要求创建并启用每 6 小时一次的 Codex 定时同步；同时保留完成工作单元后的同步方式。编辑器保存先写本地，完成 commit + push 后才会出现在 GitHub。

## 每 6 小时自动同步

- 自动化名称：`2026高教杯每6小时Git同步`；ID：`2026-6-git`。
- 类型：附着当前会话的 Codex heartbeat；创建后已回读确认状态为 `ACTIVE`，线程为 `01a08afc-ab9f-7fb2-9450-32fba83ff0a1`。
- 用户指定锚点为协调世界时 **UTC 10:00**，间隔 6 小时；当前机器时区为 `China Standard Time`（UTC+8），按下表本地时点配置。若机器时区改变，应复核调度，保持 UTC 锚点不变。

| 协调世界时 UTC | 北京时间 UTC+8 |
| --- | --- |
| 04:00 | 12:00 |
| 10:00 | 18:00 |
| 16:00 | 次日 00:00 |
| 22:00 | 次日 06:00 |

即北京时间每天 **00:00、06:00、12:00、18:00**。本次创建时已过 2026-09-10 UTC 10:00，因此下一计划时点为 **2026-09-10 UTC 16:00 / 2026-09-11 北京时间 00:00**；没有追补此前时点，也未设置自动停止日期。

每次检查本届工作区后调用现有同步脚本，提交说明使用实际 UTC 时间。无文件变化不创建空提交，但会检查并推送已有未上传的本地提交。只有实际推送和远端哈希核验通过，才记录该快照已备份。没有变化且无需处理时保持安静；有新提交上传、同步失败或需要用户操作时才通知。

定时任务避开其他 Git 操作、锁、未完成合并/变基等，不删除锁、不强推、不终止计算；对正在写入的成果先确认保存稳定。认证采用单次进程非交互设置，失败保留本地工作并报告。到点执行本地文件操作需要本机和 Codex 可运行，推送需要网络可用；创建成功不等于未来运行已完成。

## 日常使用

在 PowerShell 中运行：

```powershell
Set-Location -LiteralPath 'D:\Document\数学建模\2026CUMCM'
.\tools\git-sync.ps1 -Preview
.\tools\git-sync.ps1 -Message 'backup: A题数据审计与记录'
```

`-Preview` 只显示状态。正常运行会获取远端最新引用、检查分支与大文件、暂存所有未忽略的新增/修改/删除、创建提交、推送并比较远端提交哈希。没有文件变化时仍会推送已有的本地提交；网络失败时保留本地文件和提交，恢复网络后可重跑。推送期间继续改动的文件需再次同步。

如运行策略阻止脚本，可在本目录执行单次命令（不修改系统执行策略）：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\git-sync.ps1 -Message 'backup: 本次修改说明'
```

等价的核心 Git 操作为 `git add -A` → `git commit -m "说明"` → `git push`。该脚本额外拒绝错误远端/分支、落后于远端以及达到 100 MiB 的候选文件；不会自动合并或强推。

## 同步范围

默认纳入所有未被 `.gitignore` 排除的文件：源码、配置、数据、原始题包、来源清单、说明会、论文 Word/PDF/LaTeX、图表、结果、AI 使用记录、工作区记忆、复现/运行/审查证据、最终提交文件。现有两个原题包副本及两处解压目录均保留，未为节省空间删除原件。

仅排除：可重建缓存、虚拟环境与 IDE 机器状态、Office 锁文件、凭据，以及以下本地外部资源：

| 本地路径 | 原因与处理 |
| --- | --- |
| `.agents/skills/` | 指向父目录共享 Skill 的 Windows Junction，避免越过比赛工作区边界；采用的正式代码仍须复制到本届目录并记录来源。 |
| `B题模拟器/CUMCM2026B/Jammers-simulator/` | 外部程序目录及运行状态，保留本地；既有检查笔记继续入库。最新选题仍待定，排除该程序不表示放弃 B。 |
| `B题模拟器/CUMCM2026B/Jammers-simulator-full-win64.7z` | 外部软件包，236,850,965 字节，超过普通 GitHub 文件限制；本地保留。 |
| `B题模拟器/CUMCM2026B/Jammers-simulator-win64.7z` | 同一外部模拟器下载包，本地保留。 |
| `B题模拟器/CUMCM2026B/模拟器操作演示.mp4` | 外部演示视频，130,689,914 字节，超过普通 GitHub 文件限制；本地保留。 |

Git 不保存空目录；首次产生文件后随下一次提交加入。没有全局忽略 `.pdf`、`.zip`、`.csv`、`.log` 或 `tmp/`，以免遗漏输入和证据。不要把账号、密码、许可证、API key 放进普通文稿；`.gitignore` 仅按路径过滤，不能识别任意文件正文中的秘密。

GitHub 普通 Git 会拒绝大于 100 MiB 的单文件。后续正式数据/成果达到这一量级时，应明确配置 Git LFS 或记录可复核的外部备份位置，不能静默跳过，也不能声称这些大文件已经上传。参见 [GitHub 大文件说明](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)。当前未配置 LFS；本脚本统一拦截达到 100 MiB 的工作树文件，未来启用 LFS 时还须相应适配脚本或使用审查后的手动 Git/LFS 流程。

## 多人协作与检查

论文同学可由仓库所有者在 GitHub 的 `Settings → Collaborators` 中邀请；每人使用自己的账号和本地克隆。私有仓库链接本身不授予访问权限。尽量避免同时编辑同一个 Word/Excel 二进制文件，并用提交说明标明交接版本。

开始工作前可在干净工作区运行 `git pull --ff-only`。如果已有本地修改，先保全修改再整合远端；不要用 `reset --hard` 或 `push --force` 解决冲突。脚本发现远端有本地缺少的提交会停止，保留当前文件以便审查。

查看状态：

```powershell
git status --short --branch
git log -5 --oneline
git ls-remote origin refs/heads/main
```

最终确认必须包括 push 成功及远端 `main` 与本地 `HEAD` 一致。仅有本地 commit 不算完成 GitHub 备份。
