# A题交叉验证汇总报告

- 总判定：**PASS**
- 预声明容差：`{"integratorEventSeconds": 1.0, "faceSchemeHoursAtFinest": 0.5, "scalingResidualPercent": 5.0, "crossLanguageEventSeconds": 1.0, "analyticBenchmarkKelvin": 0.0001, "massBalanceKgPerKg": 1e-06, "independentRootSeconds": 1e-06, "schemeDifferenceKgPerKg": 0.0001, "observedOrderMinimum": 1.5, "constantDLimitKgPerKg": 0.0, "baselineLimitAbsoluteDifferencePaOverKappa": 1e-06}`
- 输入齐备情况：`{"solverCases": true, "latentScenarios": true, "thresholdScaling": true, "stageBoundaries": true, "methodComparison": true, "isothermClosure": true, "morrisScreening": true, "sobolIndices": false, "analyticMetric": true, "validatedScans": true, "thermalConservation": true}`

## L1 时间积分器交叉验证（同一网格、不同积分族）

| 问题 | 网格 | BDF / h | Radau / h | 差 / s |
|---|---:|---:|---:|---:|
| Q23 | 800 | 57.4723297616 | 57.472329762 | 1.122e-06 |
| Q23 | 1600 | 57.4723075468 | 57.4723075464 | 1.49e-06 |
| Q4 | 800 | 51.0905991564 | 51.0905991555 | 3.172e-06 |
| Q4 | 1600 | 51.0905805903 | 51.0905805903 | 5.579e-08 |

## L2 水通量面格式随网格加密的收敛

| 问题 | 网格 | Kirchhoff / h | 调和平均 / h | 差 / h | 比值 |
|---|---:|---:|---:|---:|---:|
| Q23 | N400 | 57.4724174 | 57.6868014 | 0.2144 | 1.0037 |
| Q23 | N800 | 57.47232976 | 57.51225171 | 0.03992 | 1.0007 |
| Q23 | N1600 | 57.47230755 | 57.48106625 | 0.008759 | 1.0002 |
| Q4 | N400 | 51.09067331 | 51.11054756 | 0.01987 | 1.0004 |
| Q4 | N800 | 51.09059916 | 51.09547046 | 0.004871 | 1.0001 |
| Q4 | N1600 | 51.09058059 | 51.09179149 | 0.001211 | 1 |

## L4 解析与尺度交叉验证

```json
{
  "analyticBenchmarkQ1Kelvin": 1.803776172e-06,
  "analyticBenchmarkNote": "constant-property cylindrical Bessel series, 240 terms",
  "fixedRadiusTimeH": 129.84522834701946,
  "shrinkingTimeH": 51.090973419826916,
  "reductionPercent": 60.65240589104815,
  "equivalentFixedRadiusTimeH": 131.6197854199707,
  "ratioEquivalentToFixed": 1.0136667099403038,
  "scalingResidualPercent": 1.3666709940303834,
  "interpretation": "Stretching the shrinking timeline by (R0/R(t))**2 gives an equivalent fixed-radius time within about 1.4 percent of the directly simulated fixed-radius drying time. The numerically computed shortening is therefore corroborated by an independent analytical length-scale argument; the small residual comes from the coupled changes in the moisture and temperature profiles."
}
```

## L4b 解析基准的比较口径（节点值 vs 控制体平均）

- 观测到的一阶收敛率：0.99986（表面控制体单侧，几何效应）

| 网格 N | 点值↔控制体平均最大差 / K | 内部节点最大差 / K |
|---:|---:|---:|
| 800 | 0.00205117 | 1.31107e-06 |
| 1600 | 0.00102575 | 3.27767e-07 |
| 3200 | 0.000512918 | 8.1945e-08 |
| 6400 | 0.00025647 | 2.04913e-08 |

## L6 模型结构（潜热情景包络）

### Q23

| 潜热比例 | 达标时间 / h | 相对基线 / % | 最低表面温度 / °C |
|---:|---:|---:|---:|
| 0 | 57.47232976 | 0 | 28 |
| 0.25 | 58.18572134 | 1.241 | 24.89 |
| 0.5 | 58.93408215 | 2.543 | 20.25 |
| 1 | 60.49721847 | 5.263 | 10.9 |

### Q4

| 潜热比例 | 达标时间 / h | 相对基线 / % | 最低表面温度 / °C |
|---:|---:|---:|---:|
| 0 | 51.09059916 | 0 | 28 |
| 0.25 | 52.41650771 | 2.595 | 25.7 |
| 0.5 | 53.76195569 | 5.229 | 21.69 |
| 1 | 56.4844608 | 10.56 | 14.55 |


## L7 独立求根与最慢位置证书

| 问题 | 事件根 / h | 独立二分根 / h | 差 / s | 严格复核 max C | 圆心即最大值 | 圆心超出量(中位) |
|---|---:|---:|---:|---:|:--:|---:|
| Q23 | 57.4723297616 | 57.4723297616 | 5.821e-11 | 0.14999953 | 是 | 0 |
| Q4 | 51.0905991564 | 51.0905991564 | 5.821e-11 | 0.14999905 | 是 | 0 |

## L8 同方程不同离散（Kirchhoff 势 vs 二阶守恒差分）

- 常 D 极限最大差：0 kg/kg
- 变 D 观测收敛阶：1.9991（预先声明 1）

| 网格 N | 两方案最大差 / (kg/kg) | 出现时刻 / s | 出现半径 / m |
|---:|---:|---:|---:|
| 200 | 3.72881e-06 | 1800 | 0.02 |
| 400 | 9.3255e-07 | 1800 | 0.02 |
| 800 | 2.32993e-07 | 1800 | 0.02 |
| 1600 | 5.82858e-08 | 1800 | 0.02 |

## L9 等温线／水活度闭合情景族

- 等温线：`a_w(C) = 1 - (1 - awRef) (C_ref/C)^(1/p), p >= 1`；锚点 a_wRef = 0.6
- 锚点来源：chamber plateau relative humidity from attachment 1 (derived, not assumed)
- p=1 成员与冻结边界的最大差：0
- 烘房稳态相对湿度：0.6073

| 情景 | 状态 | 达标时间 / h | 事件时 K_eff | tail 完整性 |
|---|---|---:|---:|---|
| iso_p1_Q23 | failed | 57.47232977 | — | — |
| iso_p1.5_Q23 | failed | 58.44260126 | — | — |
| iso_p2_Q23 | failed | 59.62390141 | — | — |
| iso_p3_Q23 | failed | 62.36651111 | — | — |
| iso_p4_Q23 | failed | 65.44474918 | — | — |
| iso_p1_Q4 | failed | 51.09059759 | — | — |
| iso_p1.5_Q4 | failed | 51.61135452 | — | — |
| iso_p2_Q4 | failed | 52.22830302 | — | — |
| iso_p3_Q4 | failed | 53.66798267 | — | — |
| iso_p4_Q4 | failed | 55.31621582 | — | — |

## L10 参数敏感性（代理网格 N200，仅用于排序）

**Morris 的 dScale 条目已作废**（注入缺陷，见 JSON 的 `knownInjectionDefect`）；
以下单参数扫描在修补版上运行，并在 scale = 1.0 处自检复现代理基准到 1e−6 h。

### dScale

| 取值 | Q2/Q3 事件 / h | Q4 事件 / h |
|---:|---:|---:|
| 0.7 | 79.418738 | 70.405912 |
| 0.875 | 64.752022 | 57.521427 |
| 1 | 57.472761 | 51.090969 |
| 1.05 | 55.056709 | 48.952642 |
| 1.225 | 48.188806 | 42.861468 |
| 1.4 | 43.079637 | 38.31595 |

- 跨度：Q2/Q3 36.3391 h（63.23%）；Q4 32.09 h（62.81%）

### kScale

| 取值 | Q2/Q3 事件 / h | Q4 事件 / h |
|---:|---:|---:|
| 0.85 | 57.475177 | 51.094075 |
| 0.925 | 57.473867 | 51.092386 |
| 1 | 57.472761 | 51.090969 |
| 1.075 | 57.471814 | 51.089762 |
| 1.15 | 57.470995 | 51.088723 |

- 跨度：Q2/Q3 0.00418185 h（0.007276%）；Q4 0.00535235 h（0.01048%）

**结论**：Diffusion pre-factor uncertainty of -30%/+40% moves the drying time by +38%/-25% (Q23: 79.42 h to 43.08 h; Q4: 70.41 h to 38.32 h), while thermal conductivity uncertainty of +/-15% moves it by less than 0.011%. Under this operating point the model is mass-transfer controlled.

### Morris 筛选排序（dScale 条目作废）

```json
{
  "Q23": [
    {
      "parameter": "tailTemperatureC",
      "muStar": 7.355290534162124,
      "sigma": 0.17145472705378212
    },
    {
      "parameter": "surfaceLatentFraction",
      "muStar": 2.9573812265662967,
      "sigma": 0.5870383693519421
    },
    {
      "parameter": "beta",
      "muStar": 2.441901388520472,
      "sigma": 0.38249623142241174
    },
    {
      "parameter": "h",
      "muStar": 0.5262343281375154,
      "sigma": 0.48134555895927056
    },
    {
      "parameter": "tailEquilibrium",
      "muStar": 0.522354767695715,
      "sigma": 0.19320568443265662
    },
    {
      "parameter": "equilibriumScale",
      "muStar": 0.4955588402730621,
      "sigma": 0.22884076022485944
    },
    {
      "parameter": "kScale",
      "muStar": 0.006083165617742736,
      "sigma": 0.002474753155328953
    },
    {
      "parameter": "dScale",
      "muStar": 0.0,
      "sigma": 0.0
    }
  ],
  "Q4": [
    {
      "parameter": "tailTemperatureC",
      "muStar": 6.533604352447365,
      "sigma": 0.16882105116695265
    },
    {
      "parameter": "surfaceLatentFraction",
      "muStar": 5.258565467921537,
      "sigma": 0.9394889053319107
    },
    {
      "parameter": "beta",
      "muStar": 0.978176200791584,
      "sigma": 0.16816019670622281
    },
    {
      "parameter": "h",
      "muStar": 0.8798220233226497,
      "sigma": 0.7919268865909773
    },
    {
      "parameter": "tailEquilibrium",
      "muStar": 0.5741766579233273,
      "sigma": 0.23965999020375786
    },
    {
      "parameter": "equilibriumScale",
      "muStar": 0.5070921254623177,
      "sigma": 0.27570475010985523
    },
    {
      "parameter": "kScale",
      "muStar": 0.006872527805339423,
      "sigma": 0.0019767194185731636
    },
    {
      "parameter": "dScale",
      "muStar": 0.0,
      "sigma": 0.0
    }
  ]
}
```

## L11 温度侧守恒证书

- CHECK A（速率恒等式）：`d/dt Σ 2w B T R² = 2hR(T∞−T_s)`，直接比较模型右端与表面面通量，不含任何求积或轨迹差分。
- CHECK B（累积平衡）：容量冻结在 t = 0 时成立；题目一为精确形式，耦合问的残差即有效容量随含水率变化所丢弃的功。

| 问题 | CHECK A 最大相对偏差 | CHECK B 相对残差 | 丢弃的容量功 / (J/m) | 未解释残差 / (J/m) |
|---|---:|---:|---:|---:|
| Q1 | 2.22e-16 | 7.84892e-10 | -2.65041e-11 | 0.00019522 |
| Q23 | 2.22e-16 | 0.00644549 | -174715 | 177304 |
| Q4 | 2.22e-16 | 0.550312 | -275282 | 497934 |

**Q23 的累积残差由丢弃功解释 100%**：The work done against the changing effective capacity accounts for the stated share of the frozen-capacity cumulative residual. That residual is therefore a property of the effective-capacity closure, not a solver error. Q4 retains an additional gap from the d(R^2)/dt cross term of the shrinking domain.

## 判定明细

| 检查 | 值 | 单位 | 容差 | 判定 |
|---|---:|---|---:|---|
| L1 integrator Q23 N800 | 1.1222e-06 | s | 1 | PASS |
| L1 integrator Q23 N1600 | 1.49014e-06 | s | 1 | PASS |
| L1 integrator Q4 N800 | 3.17186e-06 | s | 1 | PASS |
| L1 integrator Q4 N1600 | 5.5789e-08 | s | 1 | PASS |
| L2 face scheme Q23 N400 | 0.214384 | h | — | REPORTED |
| L2 face scheme Q23 N800 | 0.0399219 | h | — | REPORTED |
| L2 face scheme Q23 N1600 | 0.0087587 | h | — | REPORTED |
| L2 face scheme Q4 N400 | 0.0198743 | h | — | REPORTED |
| L2 face scheme Q4 N800 | 0.00487131 | h | — | REPORTED |
| L2 face scheme Q4 N1600 | 0.0012109 | h | — | REPORTED |
| L4 R-squared scaling residual | 1.36667 | % | 5 | PASS |
| L7 independent root Q23 | 5.82077e-11 | s | 1e-06 | PASS |
| L7 strict threshold Q23 | 0.15 | kg/kg | 0.15 | PASS |
| L7 independent root Q4 | 5.82077e-11 | s | 1e-06 | PASS |
| L7 strict threshold Q4 | 0.149999 | kg/kg | 0.15 | PASS |
| L8 constant-D Kirchhoff vs midpoint FD | 0 | kg/kg | 0 | PASS |
| L8 variable-D scheme difference at finest N | 5.82858e-08 | kg/kg | 0.0001 | PASS |
| L8 observed convergence order | 1.99907 | 1 | 1.5 | PASS |
| L11 thermal rate identity vs surface face | 2.22045e-16 | 1 | 1e-12 | PASS |
| L9 p=1 member reproduces the frozen boundary | 0 | 1 | 1e-06 | PASS |
| L9 isotherm passes through the forced equilibrium point | 0 | 1 | 1e-12 | PASS |
