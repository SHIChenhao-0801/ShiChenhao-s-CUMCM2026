# 本次比赛 GitHub 备份

设置日期：2026-09-10（北京时间）。用户要求本次产生的代码和文件保存在 GitHub。

- 本地仓库：`D:\Document\数学建模\2026CUMCM`，仅覆盖本届正式比赛目录。
- 远端：<https://github.com/SHIChenhao-0801/ShiChenhao-s-CUMCM2026>，分支 `main`，远端名 `origin`。
- 设置时通过已登录的 GitHub API 核实为 **private**，当前账号有推送权限。登录继续使用本机 Git Credential Manager，不将令牌写入文件。
- 保留 GitHub 原有 Initial commit；在其基础上纳入本地文件。禁止使用强制推送或清理命令覆盖团队工作。
- `.gitattributes` 禁用自动换行转换，保留文件字节和已登记的来源/结果/提交哈希；文本仍可正常查看差异。
- 每完成一个可复核工作单元，检查新增/修改/删除文件、凭据和体积后提交并推送；即使模型或稿件尚未通过验证，也可备份，提交说明须保留真实状态。Git 备份不等于模型验证、论文冻结或用户人工审查通过。
- 没有常驻后台监视器；编辑器保存只写本地，需要完成 commit + push 才会出现在 GitHub。Codex 后续按工作区约束在完成工作单元时执行同步。

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
| `B题模拟器/CUMCM2026B/Jammers-simulator/` | 已放弃选题 B 的外部程序目录及运行状态，保留本地；既有检查笔记继续入库。 |
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
