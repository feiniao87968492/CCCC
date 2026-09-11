# 共用模型主干与职责

Status: design contract; numerical validation pending. Profile: legacy.

## 共享状态

机器人状态为位置 p（米）、测向机频道 c、虚拟时间 T（秒）、墙钟剩余量 B、已清除数 K。每频道 k 维护状态 unseen / detected / cleared / certified_absent、已接受动作历史 H_k、覆盖点no_signal集合 V_k 和永久标记ever_detected。unseen替代旧名称unknown，含义不变。cleared只由成功清除反馈触发；certified_absent须完整覆盖且从未出现direction/near。detected不能因后续no_signal改判无源。Q3覆盖点为原点及半径1200米圆周的六等分点，共7点，集合固定、访问顺序在线重规划；Q4仍为81点。

源隐状态为 z_k=(G_k,r_k,type_k,psi_k)。G_k 在半径1800米圆域，r_k 在[1000,1500]米，type和psi在Q4未知；无源是独立假设。在线不读取真实隐状态。事实识别模块维护与反馈一致的集合 Z_k，位置投影为 F_k；几何实现允许保守外包 P_k，须始终保证 F_k 包含于 P_k。

## 模块分工

| 模块 | 责任 | 输出 | 消费者 |
| --- | --- | --- | --- |
| 协议与计时 | 只解释已接受动作，幂等重试不重复计数 | H_k,p,c,T,K,B | 所有策略 |
| Q1集合几何 | 纯前向楔交R的状态、直径；可行集外包另外命名 | vertices,status,diameter；P_k | Q2和清除点选择 |
| Q2主动定位 | 用Z1/F1选择下一测点，按J(q)=最坏剩余rho评价，时间单列 | q,J,travel_s,branch_sets | Q3/Q4局部定位 |
| 覆盖搜索 | 保证所有存在频道被发现；七点集合固定、顺序滚动重规划 | 下一覆盖点、V_k及覆盖证书 | 全清除终止 |
| 光学保底 | 在单次有向观测后有限步清除，不依赖朝向 | clear成功或协议矛盾 | cleared状态 |
| 评价 | 案例级统计、计时核对、预算失败与删失 | 结果表与日志 | 验证、论文 |

## 时间与决策

measure增量为距离/5 + 频道改变指示 + 5；clear为距离/5 + 3 + 2乘成功指示，clear不改变c。总时间含失败、空扫与证书建立。目标为先全部清除，再降低T；不把K最大化和T最小化任意加权。Q2主指标为最坏剩余最小覆盖圆半径rho（含no_signal），时间单列Pareto权衡。

不存在统计预测模块、学习误差分布或隐藏距离回归。误差是固定地点的有界扰动，同点复测不增加独立信息。任何几何外包失效、响应矛盾或预算不足须显式记录，不能改写成已清除。
