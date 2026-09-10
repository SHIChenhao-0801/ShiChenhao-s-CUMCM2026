# MATLAB 交叉核验源码静态交接

范围：仅新建 `paper_output/code/review_delivery/matlab/runCrossCheck.m` 与使用说明；未改原 Python、清洗数据、冻结结果或 Git。MATLAB GUI 实跑由主代理接续，本记录不是GUI运行或人工认可证据。

已逐式对照 `paper_output/code/modeling/drying_core.py` 和 `q1_model.py`、`q2_model.py`、`q4_model.py`：附录2/3/4物性、初值、环形控制体权重、中心/表面通量、Kirchhoff势、中点消减分支、4h后平台、Q4材料半径、累计干基失水、maxC事件、事件后ceil+1秒、rtol/atol/MaxStep均按同一接口实现。跨语言时间积分选MATLAB默认ode15s(NDF)+JPattern有限差分，区别已在README说明。

实际执行静态命令（cwd为本届根目录）：

```powershell
& 'D:/MATLAB/bin/win64/mlint.exe' '-id' 'paper_output/code/review_delivery/matlab/runCrossCheck.m'
```

退出码0；未报告语法错误。剩余消息为：两个最多三段的cell动态增容提醒、一次稀疏模式构造的赋值性能提示，以及三个onCleanup变量的多余NASGU抑制标记。它们没有提供算法正确性的证据，也不表示已经运行数值求解器。模式矩阵仅初始化一次，分段数量至多三段；主代理可据实测耗时决定是否值得进一步微调。

交接版本SHA256：`54cdebf6941ed139efc00ff75e43b2c5fd5a3d73d2ec095829d7bc31aae3aeda`。交接后未继续改源码，以便主代理启动GUI时保留固定版本；如运行后为修复问题修改源码，应记录新哈希并重新运行受影响case。

下一步：在MATLAB GUI运行新输出目录；验证JSON自身记录的源码/输入哈希；与同网格N40 Python独立参照对比固定时间与事件秒、全节点样本、表面水分、离散质量残差；保留GUI实际输出/错误与用户人工审查状态。跨实现一致不能替代物理预测校验或正式空间收敛结果。
