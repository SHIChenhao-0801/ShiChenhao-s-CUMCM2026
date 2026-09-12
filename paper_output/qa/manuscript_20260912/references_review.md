# 第 8 节参考文献核查与批注交接

核查日期：2026-09-12。负责文件仅为 `paper_output/drafts/sections/8.md`，编号已与第 5 章对齐。此文件记录来源核查范围，不作为团队人工审查批准书。

## 保留原文条目

[1]、[2]逐字取自用户 Word 的 P0151、P0153，仅加参考文献编号。原文、真实校正文案及一手来源完整记录于同目录 `seminar_requirements.md` 第四部分。主代理在 DOCX 对对应整条书目添加批注，不改原句。[1]应由“王乐毅、40(4):1-15”改为“王乐意、40(2):1-28”，前三作者后补“等”；[2]页码 3440-3447 正确，前三作者后补“等”。尚无授权替换记录。

## 新增条目证据及正文用途

| 编号 | 核实来源 | 可支撑的正文用途与范围 |
|---|---|---|
| [3] Crank | 原书题名页检索索引：[Bath 原书扫描件](https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf)，原页明确 J. Crank、SECOND EDITION、CLARENDON PRESS·OXFORD、1975；[GBV 保存的题名页及目录扫描](https://www.gbv.de/dms/ilmenau/toc/214048098.PDF)交叉确认题名/第二版/出版社/地点。 | 经典扩散方程与圆柱扩散解的书目依据。本轮仅取得原书页的检索索引，Bath 当前直链重定向首页，GBV 返回 429，LBL 旧链 404；未重新取得可打开的完整原书 PDF，不声称本轮逐式检查全书。正文与附录推导须由本题实际推导及数值基准自身支持。 |
| [4] Eymard等 | [Elsevier/ScienceDirect 书章页](https://www.sciencedirect.com/science/chapter/handbook/abs/pii/S1570865900070058)与[出版社提交至 Crossref 的 DOI 元数据](https://api.crossref.org/works/10.1016/S1570-8659(00)07005-8)，本地原始响应 `reference4_crossref.json`；[作者 Gallouët 的书目页](https://www.i2m.univ-amu.fr/perso/thierry.gallouet/publi.d/publi03.html)核实三作者及两位编辑。 | 支撑控制体积分、通量平衡和局部守恒。ScienceDirect 出版社摘要明确解释守恒通量构造；不据此声称本题非线性移动域方案已获得该书章的全套收敛定理。 |
| [5] FAO | [FAO 原版章节网页](https://www.fao.org/4/t1838e/t1838e0u.htm)，已打开全文。 | 支撑平衡含水率与材料、环境相对湿度、温度相关，以及内部迁移/表面蒸发的区分。该页对象是粮食，其数据或经验模型不直接移植为本题药材参数；不能据此声称气相 kg/kg 等于药材干基含水率。 |
| [6] SciPy | [SciPy 官方 solve_ivp 文档](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html)，已打开全文。 | 支撑隐式 BDF 用于刚性常微分方程、Jacobian/稀疏结构及事件检测接口的一般用法。当前网页标题是 SciPy v1.18.0 Manual，不用它代替工作区实际安装版本记录；本题运行版本由运行清单另证。 |

[4]存在一处书目源差异：作者个人书目页及旧预印本写 713—1020，ScienceDirect 当前书章页和 Crossref 出版社元数据均写 713—1018。本稿采用后者的 713—1018，并保留此差异记录，不隐去相反来源。为避免补造出版地，参考文献条目只写已核实的 Elsevier 出版社名；讲义第 72 页说明参考文献标准并非只有一种。

以上新增文献的编号用途固定为 [3] 扩散理论、[4] 有限体积、[5] 平衡含水率、[6] BDF/solve_ivp，不再增加与正文无引用关系的文献。AI工具名与模型版本不再加入参考文献，按说明会第 4、27—28 页置于 AI 支撑详情。

## AI 声明与审阅边界

第 8 节保留说明会使用过 AI 的声明结构，并据实包含资料检索、推导辅助、代码生成调试、结果核对和论文草拟，未缩写成仅语言润色。正文明确仍为团队审阅稿，没有“已逐项人工审查通过”。该状态句需待真实审阅完成后由主代理据实更新，不能仅为排版自动删去并代以完成承诺。

HTML evidence marker 仅用于关联来源核查，不代表原文 [1][2] 错误已经消失或全局文献/模型 PASS。DOCX 编排时忽略 HTML 注释，在可见书目上添加已交接的批注。
