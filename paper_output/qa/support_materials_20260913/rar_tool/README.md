# RAR 试压缩与工具来源

本次只读取完整的 `支撑材料` 目录，新增试压缩文件和证据；没有删除或修改支撑文件。425个源文件合计50,312,402字节。

| 方案 | 压缩文件 | 字节 | 创建 / 自测 | 解压SHA |
| --- | --- | ---: | --- | --- |
| 固实最大压缩 | 上级目录 `provisional.rar` | 20,329,598 | 0 / 0 | 未在此方案另做解压逐文件比对 |
| 固实最大压缩及 exhaustive search | 上级目录 `provisional_exhaustive.rar` | 20,189,014 | 0 / 0 | 实际解压425项，与源逐项字节及SHA-256一致 |

两个方案均小于20 MiB，但都大于保守的20,000,000字节上限。强方案仍高189,014字节；最终材料继续变化后必须重新打包和核验，不能把试压缩哈希当最终提交哈希。

强方案SHA-256：`a44362ee18a5eed49efb4a85771ad1a248aa462971bb8a0021ec8ef7ed1275a6`。

## 工具

- 官方页面：https://www.rarlab.com/download.htm
- 官方稳定版原始安装包：https://www.rarlab.com/rar/winrar-x64-723.exe
- 版本：RAR 7.23 x64。
- 安装包和RAR程序均经Windows Authenticode实际验签，签名者win.rar GmbH，状态Valid。
- 未执行安装器；用Windows自带tar选择性提取RAR/UnRAR及说明、许可。不修改注册，不显示GUI，不购买，不绕过许可。
- 本地工具在 `tmp/cache/support-rar/`，相对于本届工作区；QA不保留工具二进制。它们不纳入竞赛支撑包及Git版本。
- 官方EULA第2条允许最多40天免费试用；第3a条限制对除UnRAR以外单独组件的再分发。原文在缓存runtime/License.txt；来源、完整SHA及许可摘要见 `tool_source.json`。

## 最终包可采用的操作

以下以本届根目录为cwd，最终压缩路径应为一个全新的文件名；不要让最终包位于待压缩的支撑材料目录中。

```powershell
& 'tmp/cache/support-rar/runtime/Rar.exe' a -cfg- -r -m5 -md128m -s -mt4 -qo- -idq -mcx '最终新包.rar' '支撑材料'
& 'tmp/cache/support-rar/runtime/Rar.exe' t -cfg- -idq '最终新包.rar'
& 'tmp/cache/support-rar/runtime/Rar.exe' x -cfg- -idq -y '最终新包.rar' 'tmp/cache/support-rar/final_extract/'
```

每步捕获真实退出码。解压后枚举输入/解压件的所有相对路径、字节及SHA-256，集合和每项均应相等；本次可执行实现见 `try_rar.py`，逐项源清单见 `exhaustive_input_manifest.json`，实际命令、时长、退出码、零差异结果见 `exhaustive_rar_report.json`。脚本的输出只用于试包；正式重打包需另取最终文件名并保留最终输入快照。
