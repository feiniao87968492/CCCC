# 本地文献与建模边界

仅阅读用户提供的本地PDF，无联网检索、无出版社在线复核。以下是模型选择依据，不是已完成最终引用核验。文件已逐个导入user_data，插件记录其哈希；完整papers目录保持原状，不复制下载脚本或登录资料。

| 文献 | 本地页证据 | 可支持 | 不可转用 |
| --- | --- | --- | --- |
| Bishop等，Optimality analysis of sensor-target localization geometries，Automatica 46 (2010) 479-492；PDF DOI 10.1016/j.automatica.2009.12.003 | PDF第1页元数据；第2页误差假设；第8页bearing-only部分 | 几何配置影响定位信息，距离也是因素 | 第2页为独立同方差零均值高斯误差，不能据此宣称本题有界误差的概率保证或未知真位置上的精确最优 |
| Joshua Vander Hook、Pratap Tokekar、Volkan Isler，Cautious Greedy Strategy for Bearing-Only Active Localization: Analysis and Field Experiments | PDF第1页摘要；第19页Theorem 5；第24页实地误差模型 | 主动定位兼顾移动与测量耗时，初始化和误判风险重要 | 常数竞争界依赖其高斯先验、EKF与条件；不移植5.439等数值。文件名2014尚不构成出版年份核验 |
| Enric Galceran、Marc Carreras，A survey on coverage path planning for robotics，Robotics and Autonomous Systems 61 (2013) 1258-1276；PDF DOI 10.1016/j.robot.2013.09.004 | PDF第1页 | 完整覆盖与路径长度可分层设计，蛇形/覆盖扫描作为基线 | 综述不能替代本题离散射频测点的连续方向覆盖证明 |

本题P3/P4覆盖、225点保底及时间上界是本项目独立推导，不冒充上述文献中的定理。正式论文前仍须核验作者、题名、年份、DOI和出版社状态，并绑定具体支持句。

题面图像复核：已回看B题.pdf第2页图1、第3页图2，确认示向度由检测点指向G，实线两侧各1度，图2红四边形为两楔交；不是方位精确射线，也没有把源圆域画成狗的禁出区。渲染证据在evidence/problem_page2.png与problem_page3.png。
