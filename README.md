# 2026 CUMCM 正式比赛

正式工作目录：`D:\Document\数学建模\2026CUMCM`。

**2026 年 9 月 10 日 18:00（北京时间）起，本次比赛所有新增内容均在本目录进行。** 已取得正式题包，用户最终选择 A 题《药材的烘干问题》；未继承父目录练习题的完成状态。实际模型运行和门禁状态以 `paper_output/context/` 及相应证据为准。

本目录通过 Git 备份至私有仓库 [ShiChenhao-s-CUMCM2026](https://github.com/SHIChenhao-0801/ShiChenhao-s-CUMCM2026)，使用 `main` 分支。完成修改后运行 `.\tools\git-sync.ps1 -Message '本次修改说明'`；使用 `-Preview` 可先查看状态。同步范围、排除项和多人协作方法见 [GitHub 备份说明](notes/workspace-maintenance/github-sync.md)。保存到本地后还需提交并推送，才会更新 GitHub。

先读 [比赛约束](AGENTS.md) 和 [本届记忆](memoryskill.md)。用户指定最新 9 月 10 日赛前说明会为首要依据；旧资料有冲突时按该说明会更新，讲义自身不一致的事项另记待校内澄清。

| 目录 | 放置内容 |
| --- | --- |
| `problem_files/` | 2026 正式题面、原始附件和官方更新；保留原始文件 |
| `reference_materials/contest-admin/` | 最新说明会、当届行政资料和来源哈希 |
| `crawled_data/` | 围绕题意取得的外部数据及来源、时点记录 |
| `paper_output/code/` | 正式建模、清洗和出图源码、配置 |
| `paper_output/data/` | 审计及处理后的数据，原始输入可追溯 |
| `paper_output/results/` | 数值结果、指标和实际运行清单 |
| `paper_output/figures/`、`paper_output/tables/` | 可追溯图表及可编辑源数据 |
| `paper_output/paper/` | 唯一主稿、导出文件及版本 |
| `paper_output/qa/`、`paper_output/context/` | 审查证据与本次比赛工作流状态 |
| `paper_output/submission/` | 最终定稿 PDF、支撑 ZIP、哈希与提交凭证 |
| `notes/` | 比赛记录、AI 使用过程、论文交接、环境复现、自动化简报 |
| `tmp/cache/` | 可安全重建的临时缓存 |

从父项目进入：`Set-Location -LiteralPath 'D:\Document\数学建模\2026CUMCM'`。也可点用父目录 `tools/enter-2026cumcm.ps1`；为保留进入后的当前位置，在当前 PowerShell 用点调用执行。

9 月 13 日建议 19:00 前完成 MD5，硬截止为 20:00；文件上传从 20:30 开始，到 9 月 14 日 14:00 结束。上传窗口不用于修改已提交哈希对应的文件。赛后校内承诺书/纸质交付具体时刻待通知。

父目录的历史论文库与已安装工具继续作只读参考；在正式比赛中采用或修改的文件先复制到本目录并登记来源。详细准备记录入口见 `notes/reference/parent-resources.md`。
