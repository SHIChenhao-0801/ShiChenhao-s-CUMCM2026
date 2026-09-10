# 核心v5磁盘连续输出独立审查

审查对象为2026-09-10 UTC的核心v5与disk_dense.py；审查延续至北京时间2026-09-11零时。范围限定为精确存储、BDF连续查询、事件和缓存生命周期、save_run分块对齐与资料来源。没有修改源码，没有重跑大网格，没有中断正在运行的Q4。主代理随后明确授权的一次N40 Q1断点小检查已执行，证据单独保存。

**结论：D系数保存、原SciPy求值器复用、接受状态映射和采样块对齐的主体实现正确，未发现改变积分步或把缓存采样当新插值的行为。但v5存在一个已实际量化的断点选择差异，以及两个需要完善的异常生命周期路径。** 断点差异最大仅2.22e−16kg/kg，不否定已有v5收敛数值的工程意义；它使“任意查询均逐位等价”的无限定表述不成立。下列缺陷应在当前计算保存结束后修复并形成新版本，不能把新哈希倒写入v5记录。

## 1. 本次确实读取与验证的内容

- 只读disk_dense.py、drying_core.py v5、verify_dense_storage.py、verify_convergence.py、run_modeling.py相关调用和q3_model.completion。
- 只读本机SciPy1.18.1的bdf.py、ivp.py和common.py，直接核对连续多项式构造、求值和分段选择。
- 读取已有N40 Q1/Q23/Q4完整轨迹身份验证及Q23 N1600→3200全秒检查报告；没有重复它们。
- 新执行且只执行一次N40 Q1内存/磁盘配对检查，评价542个内部接受断点及左右相邻浮点时刻，共1626个查询；另在同一已求解磁盘多项式上构造正确分段选择器，没有重积分或修改求解器。
- 核对当前项目、tmp、tmp/cache和tmp/cache/solver_runs均为普通目录，没有重解析链接。未读取、删除或更改其他运行的私有缓存。

已有N40报告的PASS仍按其实际样本范围成立：三条轨迹的接受时刻/状态和事件相同，2203/2206/2206个原查询最大差为0。它未穷举每个内部接受断点，因此不能排除下面新定位的缺口。

## 2. 需要修复的具体问题

### DS-01：DiskBDF子类没有继承solve_ivp的BDF断点选择约定

位置：本机SciPy ivp.py第748、753行；项目disk_dense.py第93行的DiskBDF子类，以及drying_core.py第321行、第335行的主段/事件尾段solve_ivp调用。

SciPy在构造OdeSolution时使用精确类对象判断：

    alt_segment = True if method in [BDF, LSODA] else False

内存路径的字符串"BDF"已被转换为原BDF类，故alt_segment=True。磁盘路径传入DiskBDF类；虽然它继承BDF，但类对象并不等于BDF，因此alt_segment=False。正向时间时，前者OdeSolution.side为right，后者为left。查询恰在内部接受断点时，两者选择相邻的不同局部多项式。系数本身可以完全相同，这一分段选择仍可能产生浮点末位差。

**本次新检查的实际结果：**

| 查询组 | 点数 | 不同状态值个数 | 最大温差/K | 最大C差/(kg/kg) | 最大累计失水差/(kg/kg) |
|---|---:|---:|---:|---:|---:|
| 全部内部接受断点 | 542 | 19 | 0 | 2.220446049250313e−16 | 2.7755575615628914e−17 |
| 各断点nextafter左邻 | 542 | 0 | 0 | 0 | 0 |
| 各断点nextafter右邻 | 542 | 0 | 0 | 0 | 0 |

最大差发生于t=1723.0047355857225s、交错状态索引77；内存为1.7990894807411206，磁盘为1.7990894807411204。接受时刻、接受状态、事件及末时刻仍相同，无警告。只是另构造OdeSolution(disk.sol.ts, disk.sol.interpolants, alt_segment=True)后，全部1626个查询及所有状态分量差都变为0。私有缓存关闭后已清理，核心与存储源码哈希前后未变。

证据为同目录dense_storage_breakpoint_probe.json。它量化的是实际v5差异，不是假设未来可能发生的风险。

**建议修复：** 在每次solve_ivp返回后，对磁盘BDF结果用相同ts和现有interpolants重构OdeSolution(..., alt_segment=True)，主积分段与事件后的tail都要处理。无需改变接受数组、步长、事件值或多项式D。相比只写side="right"，按OdeSolution的alt_segment参数重构更清楚，也保留时间方向的对应逻辑。修复后扩充小型等价检查至全部接受断点及nextafter邻点即可，不需要因此盲目扩大空间网格或替换物理模型。

事件根的定位在solve_ivp内部直接调用当前单步sol，而不是事后OdeSolution的左右选择，因此这个缺口不改变原事件求根。已有Q23事件差−0.0201464s也不应归因于本项2e−16级查询差，它属于不同空间网格的数值比较。

### DS-02：收敛驱动的后处理失败没有保证Run.close

位置：verify_convergence.py第81行save_run、第82行project_run到第112行run.close。

该驱动只在成功完成保存、投影、警告检查和比较之后调用close。如果save_run写文件失败、project_run内存不足、警告被升级为RuntimeError或比较抛异常，已经成功返回的Run没有finally保证关闭。solve_case内部的异常清理无法覆盖求解函数返回之后发生的错误；进程退出可让操作系统释放句柄，但不会自动删除私有缓存目录。以目前单次BDF系数数GB的规模，失败运行可能持续占用磁盘。

这是由控制流直接确定的失败路径，本轮没有故意触发存储或内存故障，也不声称当前成功的Q4已发生泄漏。

**建议修复：** 每轮将run初始化为None，solve_case返回后的保存/投影/比较放入try，finally里调用run.close并清除引用；先确保投影结果已成为独立数组，再释放Run。正式run_modeling.py第226行附近已经采用类似finally结构，那里生命周期正确。此项主要应修收敛驱动，不能据此说所有正式输出均泄漏。

### DS-03：accepted映射在写入成功后才登记，部分写入失败时无法保证关闭

位置：disk_dense.py第52—55行。

store_accepted先open_memmap，再mapped[:]=values、flush，最后才append到accepted_arrays。如果复制或flush抛出异常，映射未进入cache.close遍历的列表。异常回溯可能仍持有局部mapped，使其底层映射保持打开；Windows删除该文件可能再抛PermissionError，遮蔽最初写入故障并留下私有目录。这是当前“失败自动清理”覆盖不全的具体代码路径，没有在本轮故障注入实测。

**建议修复：** 成功获得映射后立即登记，或者在局部try/except/finally中明确关闭未登记映射，再向外传播原异常。清理失败时保留原异常及清理异常，而不让后者完全覆盖前者。可连带将DenseCache构造时创建目录后打开文件失败的局部清理补足：当前构造发生在solve_case的try之外，若构造本身中途失败，外层没有cache对象可关闭。

这些是资源异常路径修补，不需要改变D字节、求值器或积分算法；当前已成功保存且已关闭的旧运行不因此被判数值无效。

## 3. 已确认正确的存储和查询机制

**保存的是每个真实接受步的D。** DiskBDF只覆盖_dense_output_impl，先调用原BDF._dense_output_impl。原SciPy在此取实际self.D[:order+1].copy，并包含该步的实际阶、t_old/t与h。FileBdfDenseOutput复制原对象的order、t_shift与denom，再把原D转换为本题原本使用的float64连续数组写盘。这里没有重新拟合输出点，也没有从稀疏保存场反推多项式。

**求值公式未另写一套。** FileBdfDenseOutput继承DenseOutput，输入由基类转换为NumPy时间数组；其_call_impl读取对应offset/shape的D，构造原BdfDenseOutput求值对象并调用原_call_impl。已读本机源码确认该_call_impl只用D、t_shift、denom，因此这个最小对象在固定SciPy版本下字段足够。断点左右选择发生在外层OdeSolution，正是DS-01所在。

**没有覆盖积分步逻辑。** DiskBDF不覆盖_step_impl、Newton迭代、误差估计、阶数选择或步长调整。文件读写只发生在稠密输出构造/查询，append每次先seek到bytes_written，read每次先seek指定offset；顺序事件求根读盘后，下一次append会重新定位到末端，不会接着读指针覆盖已有系数。短读会明确报错，不返回未初始化数据。

**没有新增时间重启。** 主段仍只按原有4h环境延拓边界切分，事件后仍沿用原有ceil(event_s)+1s的验证尾段。v5没有为了磁盘存储把全过程另切为许多短时积分段。已有N40接受时刻和状态逐位一致，为这一静态检查提供实际支持。

以上“精确”限定于当前实值float64模型和已核对的SciPy1.18.1私有接口；不宣称跨版本或复数ODE的通用存储协议已经验证。

## 4. 接受数组、Run生命周期与事件尾段

主段完成后先复制initial=piece.y[:,-1].copy，再把piece.y替换为accepted memmap。后续积分初值因此不依赖已经替换或将来关闭的映射视图。tail也在成功后映射并加入pieces。状态数组的行/列排列仍为原交错状态×接受时刻，没有转置写错。

Run.state按输入时间所属piece调用完整OdeSolution，保持输入顺序；没有用accepted数组线性插值代替BDF连续多项式。事件所在piece末点与tail起点重合，当前remaining掩码优先前一个piece，这与v4原来的查询规则相同。前后1e−7s的浮点边界容差也沿用旧逻辑，不由磁盘模块新增。

Run.close先清除pieces，再关闭缓存文件及登记的映射，最后删掉经检查的私有目录。关闭后不允许再使用Run查询或外部保留的映射引用，这是生命周期约定。正常路径的再次close由cache.closed保护；查询关闭Run会失败，不会把已删除缓存当有效轨迹。N40已有验证和本次小检查均实际确认私有目录消失。

solve_case对成功构造cache后的BaseException调用cache.close，覆盖积分失败、诊断失败和中断；但部分构造/映射异常及返回后的驱动异常如DS-02/03所述，不能说所有失败分支都已经清理通过。正式生产worker对每个Run使用finally，并在Q2/Q3共享同一Run完成所有输出后才释放，符合所需生命周期。

## 5. save_run分块对齐和守恒

本次逐项审查未发现数据错位：

1. times先统一形成并np.unique排序，包含常规60s时刻、指定早期时刻、数值事件与验证末时刻。
2. 每块block_times是同一times连续的128项。run.fields输出形状为“本块时间×21材料位置”；温度和浓度分别append，最后vstack恰按原时间顺序连接。
3. 同一block_times再次调用run.state，返回“完整交错状态×本块时间”。mean_C通过2w@C计算，累计量取raw[-1].copy；二者最后concatenate，均与times逐项对应。
4. 半径由完整times直接评价，长度与上述各列一致。没有块间排序、漏最后不足128项或把轴次序反过来的代码。
5. 平均C来自完整径向网格，不是由21个保存材料点重新积分；没有参考包中重复除2的问题。21点快照是辅助保存，不应取代Q4按完整Run采样固定物理半径的正式输出路径。
6. diagnostics按256个接受时刻分块，T、C、累计量来自同一raw切片；质量残差中的2w@C和累计量同时间对齐。分块可改变浮点归约末位，所以某些质量残差摘要不必逐位等于旧版一次性归约，但不表示接受轨迹发生变化。

save_run重新记录核心、解析Jacobian、磁盘模块和输入哈希，并在保存开始时与导入/加载时哈希比较。旧结果仍标其真实运行源；不要把未来v6哈希写入这些summary。诊断/保存函数本身不负责关闭Run，因为正式流程还需用同一Run导出与校验；关闭责任应由其调用者的finally承担。

## 6. 缓存路径与来源范围

DenseCache把私有目录建在ROOT/tmp/cache/solver_runs/bdf_*，使用本进程创建的独立名字，不复用其他Run缓存。当前实际路径位于D:/Document/数学建模/2026CUMCM，父层没有符号链接或junction。close校验私有目录的直接父目录与前缀，并拒绝删除子目录/符号链接条目；本轮没有执行面向其他路径的递归删除。

缓存只是可重建运行数据，不能作为最终交付或唯一结果来源；关闭后保留的是summary/输出/验证报告等正式证据。当前按单线程顺序查询同一Run，各独立运行拥有不同cache；本报告未验证同一文件句柄的并发线程访问，也没有要求为未使用的并发方式新增改造。

磁盘机制来自本队源码与本机SciPy原求值器，没有使用外来参考代码、pickle或隐藏缓存。SciPy私有API依赖是版本条件，后续升级应重新核对字段和分段策略；DS-01也说明“继承了BDF”不自动继承调用方所有类判断。

## 7. 已有Q23细网格记录能支持什么

读取Q23_final_resolution_v5/convergence_report.json：N1600和N3200同一物理/离散设置，均无求解警告；比较206903个整数秒、21个固定物理半径位置，最大温差2.8929259201504465e−6K，最大C差3.830289061168557e−5kg/kg，后者在t=1s、表面。事件差为−0.020146428927546367s。

这说明磁盘实现已经实际支持本轮较细完整轨迹和全秒查询，不能把它称为空白方案。该报告的比较网格和时间集合明确，不能泛化成所有连续半径、任意连续时刻的严格误差界。它也不能取代DS-01所针对的机器级任意查询一致性检查。Q4在本审查期间仍由主代理运行，不在这里补写尚未冻结的结果。

## 8. 来源哈希与交付状态

| 实读来源 | SHA-256 |
|---|---|
| drying_core.py v5 | 325a17c9da48f2ed04f74c1cc7576104449b3340d856f87a181f746d674b70a8 |
| disk_dense.py | 2a886c39b7d287ce0cccac7850051583d3205a2f9032ba94b0cc04212afacb06 |
| verify_dense_storage.py | cc065b2a3963650115b3d267f43b6c69054e73cf3975a9c4411b5703ba56a9fa |
| verify_convergence.py | d0a7ece6d0b3a360656a693dbd29207f5adc3c7a90fe6165a555ff12dd53a80d |
| run_modeling.py读取快照 | 1770dc580f54a932f5854b6e5bb211efbc72f7db162858b6aacccec6d82683a6 |
| N40原身份验证verification.json | a14ac04fa9ae6b35b300bf711eb5dabe7c14a94d0bae280f20abf33bc09e4bdb |
| Q23 v5收敛报告 | 0fe5a791f3df2dff3b29c0bcc4a0e527da6f7330570f5144c2f573bc4781a579 |
| 本次断点小检查JSON | 8a9742dd68952341bc4231e1cea412676a68be2c3a964476bf6cbff559426499 |

源码与报告的读取/后续版本可能不同，因此所有结论限定在上表快照。新小检查已关闭全部Run并清除自身缓存；审查者没有保留live Run，不再调用save_run。本报告没有修改完整建模主稿或冻结101公式分支，没有新增物理公式。修复与新版验证由主代理在当前计算保存后进行，VS GUI与用户人工审查状态继续分开记录。
