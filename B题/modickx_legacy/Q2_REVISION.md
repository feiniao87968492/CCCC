# Q2分层鲁棒选点修订

用户指定重构Q2为分层鲁棒选点，不授权进入正式测试。原模型检查点仍为waiting_review；本文件只记录设计文档变更。Q1半平面交、第4节225点SAFE、Q3七点覆盖、Q4定向覆盖保持原文。

当前Q2：第一次direction后建立联合状态Z1=(g,r)，位置投影F1；r在两次检测中为同一未知常数。检测可靠性分F_full_1000（保守1000米全覆盖）与C_guaranteed（利用r>=max(1000,||g-s||)的精确保证区），二者不得混用。对每个候选q必须更新near / direction(b) / no_signal三分支；no_signal的位置投影为F_no(q)={g in F1: ||g-q||>max(1000,||g-s||)}，禁止写成F1减去1000米圆。主指标J(q)=可行反馈上rho的最坏值；移动时间||q-Sd||/5单列Pareto。90度交会只作启发式。

第二轮修订（候选生成）：完整2°×1500m扇形的MEC半径rho0=1500/(2 cos 1°)≈750.114m，这是F1的几何尺度上界，不是接收半径。程序对具体F1求B(c1,rho1)，C_core=B(c1,1000-rho1)，且C_core ⊆ F_full_1000 ⊆ C_guaranteed。删除以s为心的20–3000m固定极坐标网格；改为A层C_core、B层C_guaranteed\C_core、C层保证区外200–400m环带。c1不是最终q*。局部精修只在优胜区域进行。

本修订为设计文档变更，无求解策略代码已存在，不生成或运行模拟器策略。连续min_q J(q)未给出全局最优算法。

第三轮（验证，不改选点主算法）：新增 `src/q2_validation.py` 真值 oracle 与 `tests/test_q2_*.py`。一级门：z_true∈Z_k、C_core 保证、rho≤20 才可 certified_clear；失败码 MODEL_OR_IMPLEMENTATION_ERROR。详见 docs/Q2验证框架.md。
