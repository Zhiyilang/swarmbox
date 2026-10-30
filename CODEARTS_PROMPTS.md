# 华为云码道（CodeArts）使用提示词清单 — SwarmBox

> 用途：解决华为智能体创新赛（北部赛区）「码道深度使用 **25 分**」卡点。
> 官方评分细则逐字：「码道在开发全流程的覆盖度（**环境搭建、代码生成、调试排错、文档生成**等）」＋「Prompt 设计质量与工具使用效率」＋「使用证明材料的完整性与真实性」。
> 本清单按这四项编排，并针对 SwarmBox 的**真实符号**设计（`gate.py` 的 `screen()` / `check_shape()` / `check_identity()` / `check_state()`、`ledger.py` 的 `class Ledger`、`world.py` 的 `class World` 与 `InvariantError`、`fidelity.py` 的 `aggregate()` / `compare()`）。
> **每条执行一次 → 截图一次**，全部放入 `codearts_proof/`。

---

## 操作方式

1. 登录华为云码道：`https://developer.huaweicloud.com/codeartsco.html`，打开 SwarmBox 工程。
2. **逐条复制下面「提示词」框内原文**粘贴发送。
3. 每条保存 3 张图：① 对话与 Prompt 原文 ② 码道回答/生成代码 ③ 本地执行结果终端。
4. 保留码道 IDE 插件的**操作日志与记录**（官方明确列为证明材料）。
5. 💡 中部（PayPilot）、西北（QuorumPilot）、北部（SwarmBox）**三单可在同一场码道会话连做**，切换工程目录即可，三组截图分别归档。

---

## A. 环境搭建

### A1 — 一键安装与环境自检

**提示词：**
```
这是我的项目 SwarmBox（多智能体不可逃逸测试床，纯 Python 标准库、零第三方依赖、
零网络访问，Python 3.9+）。
结构（真实模块名）：根目录 eval.py、eval_chain.py；包 swarmbox/ 下有
__init__.py、__main__.py、agents.py、chain.py、fidelity.py、gate.py、ledger.py、
metrics.py、probe.py、swarm.py、world.py。

请生成两个文件：
1) scripts/setup.sh —— 一键环境搭建：检测 Python >= 3.9、创建虚拟环境、安装依赖
   （本项目无第三方依赖，脚本应说明这一点并跳过安装）、打印自检结果。
2) scripts/doctor.py —— 环境自检：Python 版本、swarmbox 包可导入性、eval.py 可
   执行性，每项以 PASS/FAIL 打印并以退出码反映结果。

约束：只使用 Python 标准库；Windows 与 Linux 均可运行（Windows 用 python 命令）。
输出完整文件内容。
```

**截图**：对话 + 脚本 + 跑 `python scripts/doctor.py` 的终端输出。

---

## B. 代码生成

### B1 — 为闸门新增一类校验

**提示词：**
```
阅读 swarmbox/gate.py，重点是：
- check_shape(prop)
- check_identity(prop, agent_id)
- check_state(prop, world, agent_id)
- screen(prop, world, agent_id)  ← 汇总闸门

请新增第四重校验「速率校验 check_rate(prop, world, agent_id)」：
- 需求：限制单个智能体在单位轮次内的提案数量，超出则拒绝，reason/rule id 使用
  RATE_LIMIT。
- 必须挂进 screen() 的校验链，且保持现有三重校验的顺序与语义不变。
- 被拒提案仍需写入 ledger（与现有行为一致）。

约束：纯标准库；**不得引入任何可被智能体输出影响的参数**（速率阈值必须是世界
配置的一部分，不是提案内容）；给出完整改动代码，以及追加到 eval.py 的新断言
（要求 `python eval.py` 仍全绿并说明断言数变化）。
```

**截图**：对话 + 生成代码 + `python eval.py` 新结果。

### B2 — 扩展攻击语料

**提示词：**
```
阅读 swarmbox/probe.py 与 eval.py 中攻击语料（corpus）的定义方式。

需求：现有 32 条攻击语料覆盖文件/网络/进程/import/反射等逃逸尝试。请再补充
8 条**新型**逃逸尝试语料，方向建议：NFKC 归一化绕过、控制字符注入、深层嵌套结构
膨胀、超大整数/浮点边界、Unicode 同形字伪装身份、空字节截断、递归引用、
时间戳伪造。每条需标注**预期命中的规则 ID**。

约束：纯标准库；给出完整语料代码与对应的新断言；说明新增后 corpus 总数与
`python -m swarmbox gate` 的预期输出（当前为 32 items / 31 命中预期规则 /
escape successes 0）。
```

**截图**：对话 + 生成语料 + `python -m swarmbox gate` 新输出。

---

## C. 调试排错

### C1 — 定位并修复一个真实缺陷

**提示词：**
```
问题：swarmbox/gate.py 的 check_identity(prop, agent_id) 在遇到 Unicode 同形字
（homoglyph）伪装的 agent_id 时，行为不稳定——有时判为同一身份，有时判为不同。

请：
1) 定位导致不稳定的具体代码位置（给出行号与原因，例如未做 NFKC 归一化或比较
   时未规范化）；
2) 给出修复方案（建议：比较前统一做 NFKC 归一化，并明确"归一化后相等即视为
   同一身份"的语义）；
3) 给出修复后的完整代码片段；
4) 给出回归断言锁死该行为（含至少一组同形字正反例）。
```

**截图**：对话 + 定位与修复代码 + 修复后终端输出。

### C2 — 解释与优化

**提示词：**
```
这是 swarmbox/world.py 的全文（粘贴），重点是 class World 与 class InvariantError。
请：① 解释公共资源池与不变量（invariants）的维护机制，以及违反时如何抛出
InvariantError；② 说明为何 "invariant violations 0" 是可证明的工程性质而非
统计巧合；③ 给出异常处理、日志、可读性方面的具体优化建议。
```

**截图**：对话 + 解释与建议。

---

## D. 文档生成

### D1 — 架构与复现文档

**提示词：**
```
阅读 swarmbox/ 全部模块、eval.py、eval_chain.py、REPORT.pdf 对应内容。
请生成：① 一份中文架构说明（模块依赖图 + 提案流转数据流 + "不解释执行、只作
数据解析"的不可逃逸设计 + 只追加账本的可审计性）；② 一份复现指南（如何
git clone 后一键跑出 235 条断言、gate/run/fidelity 三条命令各自验证什么）。
输出 Markdown，可直接放进 readme/ 目录。
```

**截图**：对话 + 生成的 Markdown。

### D2 — 部署运行与实验说明

**提示词：**
```
阅读 swarmbox/fidelity.py 的 aggregate(metrics_list) 与 compare(n=..., rounds=...)、
swarmbox/metrics.py、swarmbox/swarm.py。
请生成实验说明文档：如何配置 5–20 个智能体、如何跑对照实验、collapse_rate /
gini / collusion corr 等指标各自的含义与判读方式、如何解释 −0.831 这类合谋
相关系数。输出 Markdown。
```

**截图**：对话 + 生成的文档。

---

## 交付自检（打包前确认）

- [ ] A 组 ≥1 条（含脚本与执行输出截图）
- [ ] B 组 ≥2 条（含生成代码与 eval/gate 结果截图）
- [ ] C 组 ≥1 条（含定位过程与修复后结果截图）
- [ ] D 组 ≥2 条（含生成的 Markdown）
- [ ] 码道 IDE 插件**操作日志/记录**已导出
- [ ] 图片命名可读（如 `codearts_proof/B1_check_rate_01.png`）
- [ ] 所有截图为**真实操作记录**，不做任何合成或伪造
- [ ] `video/` 已放入 60–90 秒演示录屏（见主文档第 6 节）
