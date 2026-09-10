# 本轮私有Git备份预检

本预检只读执行，未add、commit、push或删除任何文件。扫描根目录为 `D:/Document/数学建模/2026CUMCM`，Git实际仓库根目录也为此目录。没有扫描父目录其他项目、全局凭据目录或Git内部对象。机器可读的起止时间、逐文件路径/大小/扫描分类/命中计数见同名JSON。

**本轮候选文本与大小预检没有发现需要阻止备份的命中项。这个结论限定于下述候选范围和文本规则，不能解释为二进制、压缩包或整个工作区已经证明不含秘密。** 此报告不代表已提交或已推送。

## 扫描范围与计数

候选集合是 `git diff --name-only --relative HEAD -- .` 的本轮已跟踪变更，加 `git ls-files --others --exclude-standard -- .` 的未跟踪且未被忽略文件。使用NUL分隔读取路径，内容扫描只打开解析后仍位于本仓库内的普通文件；没有追踪到其他工作区。

| 项目 | 计数或大小 |
|---|---:|
| 扫描开始时已跟踪变更 | 9个路径 |
| 扫描开始时未跟踪、未忽略文件 | 1119个路径 |
| 去重候选 | 1128个文件 |
| 候选总大小 | 416287437字节 |
| 已扫描文本 | 831个文件 |
| 二进制/压缩文件，未解析内部 | 297个文件 |
| 不可解码文本 | 0 |
| 大于100MiB（104857600字节） | 0 |
| 候选.env或凭据样式文件名 | 0 |
| 候选中的.git内部路径、意外嵌套仓库、临时/可重建缓存路径 | 0 |
| 读取错误、越界引用、扫描期间观察到的文件变化 | 0 |

这里的0只针对上述候选，不代表被.gitignore排除的缓存/.env不存在，也不代表未修改的已跟踪文件均已检查。扫描前后文件集合刷新时只新增本预检JSON，未移除候选；本Markdown随后生成。主代理仍可能继续写稿件或GUI记录，因此这是一份有时间戳的快照，后续新内容不自动继承检查结论。

## 凭据与调试令牌规则

已对文本检查私钥头、常见GitHub/OpenAI/AWS/Slack令牌样式、JWT、Authorization字面量、URL嵌入凭据及常见密钥/密码字段字面量。也按文件名标记.env、私钥/证书容器和凭据样式文件。没有命中需复核的候选；没有输出或保存任何匹配文本、令牌值或秘密片段。

对Visual Studio/debugpy访问令牌，另扫描客户端/服务器/适配器access-token参数及命名字段，并补查引号、逗号、反斜杠或等号包围的参数表示。831个文本文件复查后实际令牌模式命中数仍为0。`notes/A-modeling/2026-09-10/gui_final_v6a/gui_observation.md`含1处调试相关术语，单独的术语出现不等于凭据内容。

另在32个文件中发现64处项目求解批次的launch校验随机值，已在JSON逐路径计数。它们出现在版本launch、process_result、case_record、run_manifest、time_accuracy_report和引用这些记录的审计JSON中，属于本地运行来源校验参数；没有将它们自动当成外部服务凭据或VS调试访问令牌，也没有输出其实际值。不要为消除字符串匹配而擅自改写已冻结证据及其哈希；具体备份处理仍由主代理统一决定。

涉及的主要路径族为：

- `notes/A-modeling/2026-09-10/data/autoresearch_final_review.json`
- `notes/A-modeling/2026-09-10/data/final_numerical_audit.json`
- `paper_output/results/gui_reproduction/gui_final_v6a/`
- `paper_output/results/production/final_v6a/`
- `paper_output/results/time_accuracy/`
- `paper_output/results/model_results.json`
- `paper_output/results/run_manifest.json`

## 二进制与授权资料边界

297个二进制/压缩文件包括截图、PDF、Excel、Word、ZIP、NPZ等。本预检没有解压其内部、反序列化pickle、执行外来代码或对截图做逐图秘密内容检查，不能声称这些文件“无秘密”。其文件路径、大小和跳过原因已保留。

正常赛题与数据、用户授权保存的微信Word/参考ZIP、建模证据及项目聊天身份均在用户授权备份范围；本预检不会仅因出现姓名、学校、聊天身份或参考资料便自动判为凭据。备份预检也不代替最终公开提交材料的匿名性审查。

本轮无需因本次文本/大小扫描发现而删改原始数据或冻结结果。备份执行、最终文件选择、提交和远端一致性核验由主代理完成；本子任务未操作Git索引和远端。

