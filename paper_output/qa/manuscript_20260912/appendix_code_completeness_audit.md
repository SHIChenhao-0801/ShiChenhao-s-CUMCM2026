# 附录D/E完整源码与匿名文字静态审计

判定：PASS_STATIC_SCOPE。42份完整源码，共9434行；原11份2994行，补充31份6440行。

逐份核对源文件原始字节SHA256与两manifest；再将文件按UTF-8解码，只统一换行符（如有BOM则去除），与Markdown代码块逐字符、逐行比较。未裁剪尾部空行，未忽略空格，未只做关键函数抽样。原始源码哈希和统一换行后的源码/代码块哈希在JSON分别保存。

|Markdown|代码块/代码行|逐行结果|E范围及勘误|历史槽位|
|---|---:|---|---|---|
|paper_output/drafts/sections/appendix.md|42/9434|全部一致|31项全部显示|已显示|
|paper_output/drafts/assembled_draft.md|42/9434|全部一致|31项全部显示|已显示|
|paper_output/final_paper_source.md|42/9434|全部一致|31项全部显示|已显示|

采用范围核对限定在每个E文件自身的代码块前说明：31项采用范围全部显示，所有非空note逐字显示，历史版本原槽位全部显示。敏感性仅采纳修复后D/k、经验阻力仅采纳Kp事件、热侧仅采纳B*Tdot瞬时恒等式的必要勘误均已随完整源码列出。

匿名文字扫描未发现已知用户名Shi Chenhao/SHIChenhao、福州大学/厦门大学及其英文缩写、Windows用户目录、邮箱、含团队账户的GitHub标识。检出的两条URL均为正文官方文献来源，均不在代码块内；普通D盘项目目录保留，不含上述身份词。此结论只覆盖正文/源码可见文字，不包含DOCX/PDF元数据或所有可能的间接身份线索。

assembled_draft与final_paper_source全文存在正文编辑差异，但42份代码块在两个版本均完全一致。对全文编辑差异本轮没有另作模型重审。所有被检查文件在脚本读取至复核结束期间保持相同字节。

本轮没有运行科学程序、没有修改正文/源码/清单、没有操作Git；DOCX仍在组装，本报告没有冒称DOCX/PDF视觉或人工审查通过。

|附录项|源码|行数|最终Markdown代码围栏行|
|---|---|---:|---:|
|D.1|paper_output/code/modeling/run_modeling.py|448|925|
|D.2|paper_output/code/modeling/q1_model.py|8|1380|
|D.3|paper_output/code/modeling/q2_model.py|8|1395|
|D.4|paper_output/code/modeling/q3_model.py|27|1410|
|D.5|paper_output/code/modeling/q4_model.py|8|1444|
|D.6|paper_output/code/modeling/drying_core.py|402|1459|
|D.7|paper_output/code/modeling/analytic_jacobian.py|325|1868|
|D.8|paper_output/code/modeling/disk_dense.py|121|2200|
|D.9|paper_output/code/modeling/export_outputs.py|748|2328|
|D.10|paper_output/code/modeling/publication_plots.py|402|3083|
|D.11|paper_output/code/modeling/production_provenance.py|497|3492|
|E.1|paper_output/code/modeling/validate_bessel.py|345|4002|
|E.2|paper_output/code/modeling/compare_analytic.py|242|4356|
|E.3|paper_output/code/modeling/verify_convergence.py|127|4605|
|E.4|paper_output/code/modeling/verify_time_accuracy.py|251|4739|
|E.5|paper_output/code/modeling/verify_dense_storage.py|69|4997|
|E.6|paper_output/code/modeling/run_experiments.py|74|5075|
|E.7|paper_output/code/verification/crossvalidate_solver.py|206|5156|
|E.8|paper_output/code/verification/method_comparison.py|197|5371|
|E.9|paper_output/code/verification/threshold_and_scaling_checks.py|175|5577|
|E.10|paper_output/code/verification/energy_balance_check.py|245|5761|
|E.11|paper_output/code/verification/sensitivity_analysis.py|292|6015|
|E.12|paper_output/code/verification/isotherm_activity_closure.py|494|6316|
|E.13|paper_output/code/versions/verify_convergence_v1.py|106|6819|
|E.14|paper_output/code/versions/verify_convergence_v5.py|123|6936|
|E.15|paper_output/code/versions/drying_core_v2_kirchhoff.py|326|7068|
|E.16|paper_output/code/versions/drying_core_v3_analytic_jacobian.py|338|7403|
|E.17|paper_output/code/versions/drying_core_v5_disk_dense.py|395|7752|
|E.18|paper_output/code/versions/disk_dense_v5.py|99|8156|
|E.19|paper_output/code/versions/run_experiments_v1.py|73|8266|
|E.20|paper_output/code/versions/drying_core_v1_harmonic.py|296|8348|
|E.21|paper_output/code/review_delivery/matlab/runCrossCheck.m|495|8651|
|E.22|paper_output/code/review_delivery/tools/compareMatlab.mjs|200|9153|
|E.23|paper_output/code/review_delivery/runLogged.ps1|50|9362|
|E.24|paper_output/code/review_delivery/runDelivery.py|281|9421|
|E.25|paper_output/code/review_delivery/dryingCore.py|420|9709|
|E.26|paper_output/code/review_delivery/analyticJacobian.py|333|10136|
|E.27|paper_output/code/review_delivery/diskDense.py|128|10476|
|E.28|paper_output/code/review_delivery/q1Model.py|10|10611|
|E.29|paper_output/code/review_delivery/q2Model.py|10|10628|
|E.30|paper_output/code/review_delivery/q3Model.py|30|10645|
|E.31|paper_output/code/review_delivery/q4Model.py|10|10682|
