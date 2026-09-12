# 六图独立Word的数据复核

结论：**数据核验通过；建议收紧三处路径/记录条数措辞。** 未发现需要改变绘图数值、模型设置或六图内容的错误。只读已有资料，没有重跑模型、渲染或修改现有论文/清单。

## 应在独立Word中明确的措辞

- 图2写“241条数据记录，另有1行表头”，避免把241理解为CSV总行数。
- 图3两张核对表应完整写为 `paper_output/results/production/final_v6a/outputs/q2_paper_temperature.csv`、`paper_output/results/production/final_v6a/outputs/q2_paper_moisture.csv`；outputs不是Q23的子目录。
- 图5写“145条数据记录，另有1行表头”。

## 重点复核结果

| 项目 | 实际复核 | 结论 |
|---|---|---|
| 图2观测 | A_environment_observed.csv，241条，5字段，间隔60 s；末点t=14400 s、50.165°C、0.04986 | 正确 |
| 图2延拓 | 源码条件严格为t>14400 s；t=4 h仍保留实测末点，之后50°C、0.05 | 正确；开闭端点需明确 |
| 图4全域最大值 | fig_q3_drying_data.npz有266个时刻，max_C生成时取全体生产节点最大值 | 正确；不用21点抽样最大值替代 |
| 图4严格报告 | t_c=206900.28702201758 s；t_r=206900.64 s；max_C(t_r)=0.14999989718225315 | 正确；t_r不在采样NPZ，须从summary取点 |
| 图4结束范围 | 已有轨迹到206902 s，约57.47278 h | 60 h仅为轴范围，末段留空 |
| 图5采样 | Q4保存3069×21；0、6、12、24、48 h及183926.06923258994 s均精确存在 | 正确；r=material_x×radius_m[i] |
| 图5半径 | 六时刻半径依次2、1.374、1.248、1.204、1.2、1.2 cm；附件0–72 h | 正确；不需半径外推 |
| 图6 | scenarios六条全部N800、latent=0、computed_event_only，取顶层event_h | 路径、参数与六个数值全部正确 |

图4若使用采样NPZ补局部显示，应标为中心/表面样点连线；全域max曲线仍取专门max_C字段。本轨迹中心与全域max在已有图数据上最大差4.44×10⁻¹⁶，属于数值舍入，不据此改写一般全域最大值定义。

图6核对数值：

| p | Q23临界时长/h | Q4临界时长/h |
|---:|---:|---:|
| 1 | 57.47232976256206 | 51.090599155463806 |
| 2 | 59.623901353233975 | 52.22830295685303 |
| 4 | 65.4447491379564 | 55.31621495305313 |

共核对20个文件，全部存在；原先17个已记录数据文件当前SHA与上一轮完全一致。当前SHA、字段、CSV数据条数、NPZ数组形状及代码定位全部写入同名JSON。以下仅列主要文件校验指纹，完整清单见JSON：

| 文件 | SHA-256 |
|---|---|
| paper_output/data_cleaned/A_environment_observed.csv | `e4994c5cb38e4433afc927de72500bbdd15315b203e7997ba59fc6c9dfab9af0` |
| paper_output/data_cleaned/A_radius_observed.csv | `bbb5b0aac31ede1173521183d81e8d55b7ed1012e1869fbb3eef50166801470c` |
| paper_output/results/production/final_v6a/Q23/summary.json | `d5cf14f9e69405006e9636cdffd70b1d3dca7811ffa822638a76205f9bcd1346` |
| paper_output/results/production/final_v6a/Q4/sampled_solution.npz | `953db94a659d0ae4f4a9830aa2e14c10b2460fd19a15963ff5cf222f8f2f5518` |
| paper_output/results/crossvalidation/isotherm_closure_v1/isotherm_closure.json | `7528cf2deb3b596c4c1877ad291043a3e47c8e96127de03cbb760a2ee63f9c96` |

现有论文、原清单、正式结果和模型代码均保持只读。
