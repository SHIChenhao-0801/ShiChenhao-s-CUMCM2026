# 2026-09-11 日出软目标与环境参考

记录时间：2026-09-11 03:19—03:24（北京时间，UTC+08:00）。用途仅为本轮代码工作的时间安排，不属于 A 题模型输入、结果或比赛交付截止时间。

**本轮采用的日出软目标：2026-09-11 北京时间约 05:52。** 用户允许超过这个时间继续完善；不得为赶日出跳过实际运行、数值检验、运行日志或人工审查准备。

## 地点和来源

用户指定厦门高崎国际机场 05/23 跑道中心点。公开机场数据库 [Airport Guide：XMN 跑道资料](https://airportguide.com/airport/info/XMN) 给出 05 端约 `(24.53459930419°N, 118.11499786376°E)`、23 端约 `(24.55340003967°N, 118.14099884033°E)`；将两端经纬度分别取均值，得到用于排程的近似中点：

`latitudeDeg = 24.54399967193; longitudeDeg = 118.127998352045`

对外仅报告 **24.5440°N、118.1280°E**。这些端点来自公开机场数据库，不是本轮核验过的当期官方航行资料；原始小数位数不能解读为定位精度。[SkyVector 的 ZSAM 索引](https://skyvector.com/airport/ZSAM/Xiamen-Gaoqi-Airport)列出的跑道两端坐标略有差异，且列有内移入口，故不冒称取得厘米或米级的法定跑道中点。此处近似足够支持以分钟安排工作的需求。

[CAAC ZSAM AD2.24-1 航图历史镜像](https://opennav.com/pdf/ZSAM/ZSAM-1.pdf)由中国民用航空局署名，日期为 2013-09-15，载有 05/23 跑道、3400×45 m、两端入口分别内移 150 m/200 m 等信息；本轮把它作为跑道身份和“跑道端点不等于内移着陆入口”的背景核对，**没有当作 2026 年有效航行资料或精确中点坐标来源**。

## 日出计算与交叉核对

使用 [NOAA《General Solar Position Calculations》](https://gml.noaa.gov/grad/solcalc/solareqns.PDF)公开的简化季节谐波公式，2026 年非闰年，9 月 11 日是第 254 日；以当天中午求季节参数，标准日出天顶角取 `90.833°`，其中约 `0.833°` 包含太阳视半径与近地平折射修正。结果采用北京时间 UTC+08:00，无夏令时。

计算假设海平面水平、无遮挡地平线，不另加机场标高、观察者眼高、山体、建筑遮挡、实时气压温度或云层修正。此结果是标准天文日出估算，不能保证用户实际最先看到太阳的时刻。NOAA 的[计算说明](https://gml.noaa.gov/grad/solcalc/calcdetails.html)也说明真实大气条件会使观测时刻偏离计算，且网页工具目前不再积极维护；本记录使用其公开公式，不把网页运行状态当作计算证据。

以下 JavaScript 算术已在本轮工具执行器中实际运行；没有安装额外包，也没有新增 Python/C++ 程序：

```javascript
const latitudeDeg = (24.53459930419 + 24.55340003967) / 2;
const longitudeDeg = (118.11499786376 + 118.14099884033) / 2;
const degToRad = Math.PI / 180;
const dayNumber = 254;
const localHour = 12; // 使用中午参数作日期级近似
const fractionalYear = 2 * Math.PI / 365 *
    (dayNumber - 1 + (localHour - 12) / 24);
const equationOfTimeMin = 229.18 * (
    0.000075 + 0.001868 * Math.cos(fractionalYear)
    - 0.032077 * Math.sin(fractionalYear)
    - 0.014615 * Math.cos(2 * fractionalYear)
    - 0.040849 * Math.sin(2 * fractionalYear));
const declinationRad = 0.006918
    - 0.399912 * Math.cos(fractionalYear)
    + 0.070257 * Math.sin(fractionalYear)
    - 0.006758 * Math.cos(2 * fractionalYear)
    + 0.000907 * Math.sin(2 * fractionalYear)
    - 0.002697 * Math.cos(3 * fractionalYear)
    + 0.001480 * Math.sin(3 * fractionalYear);
const sunriseHourAngleDeg = Math.acos(
    Math.cos(90.833 * degToRad) /
      (Math.cos(latitudeDeg * degToRad) * Math.cos(declinationRad))
    - Math.tan(latitudeDeg * degToRad) * Math.tan(declinationRad)
) / degToRad;
const sunriseLocalMinutes = 720
    - 4 * (longitudeDeg + sunriseHourAngleDeg)
    - equationOfTimeMin + 8 * 60;
```

实际浮点输出为：`equationOfTimeMin = 3.151970808613365`；`declinationDeg = 4.868093435556099`；`sunriseLocalMinutes = 351.73998950523935`，即约 `05:51:44`。秒位仅保留为计算可复核记录，**排程只采用约 05:52，不宣称秒级预测精度**。把季节参数求值时间改为约 05:52 后，简化式得到约 05:51:39，仍按分钟落在 05:52；这不是对真实日出的严格误差上界。

[timeanddate 的厦门 2026 年 9 月太阳历](https://www.timeanddate.com/sun/china/xiamen?month=9)明确列出 9 月 11 日日出 **05:52**，当地民用曙光始于约 05:29。该城市参考点不是本轮跑道中点，只用于分钟级独立交叉核对；本轮“日出”采用 05:52，而没有把更早的曙光混作日出。读取页面时已确认标题为“September 2026”，避免使用页面顶部缓存的“今天”数值。

## 已有环境证据的只读核对

证据入口为父工作区 `D:/Document/数学建模/notes/environment/2026-09-10-verification-and-acceptance.md`（只读）。以下是既有实际验证记录，不代表本子任务重新运行这些软件：

| 工具 | 已记录版本及路径 | 既有证据范围 |
|---|---|---|
| Python | 3.14.7；`C:/Python314/python.exe` | VS 小样断点、单步、变量与继续运行；NumPy/SciPy/pandas/Matplotlib/scikit-learn 已有导入证据 |
| MATLAB | R2026a Update 5；`D:/MATLAB/bin/matlab.exe` | GUI 小样；回归、线性方程、绘图、`ode45`、`linprog`、`fitlm` |
| R | 4.6.1；`D:/R-4.6.1/bin/Rscript.exe` | Rscript 小样回归、线性方程和 CSV/PNG 输出 |
| Visual Studio | Community 2026 18.10.0；安装版本 18.10.12201.205；`D:/VisualStudio/Common7/IDE/devenv.exe` | 已启动并对 Python/C++ 小样完成源码查看、断点、单步、运行 |
| C++ | MSVC 14.51.36231 / v145 / SDK 10.0.28000.0 | Debug x64 小样编译运行成功；不能据此推定正式算法已验证 |
| Java / IntelliJ IDEA | 本次检索的环境记录内未找到明确版本、安装路径或实跑证据 | 不将“未在记录找到”写成“未安装”；如正式需要应由主代理另核查 |

正式 A 题既有 GUI 观察记录为 `notes/A-modeling/2026-09-10/gui_final_v6a/gui_observation.md`，记载 VS 中的 Python 项目与解释器；本任务没有操作 GUI、没有改动这些记录，也没有把既有运行或 AI 检查充当用户本人代码签核。
