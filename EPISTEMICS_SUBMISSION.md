# AI×Epistemics Research Sprint 2026 — 提交包（SwarmBox · Track 2 Trust Infrastructure）

> **赛事**：AI×Epistemics Research Sprint 2026 · Apart Research
> **官方页**：https://apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15
> **时间**：2026-11-13 ~ 11-15（线上）
> **提交截止**：**Sunday, November 15, 2026, 11:59 PM AoE** → 北京 **11-16 19:59**（AoE=UTC−12）
> **奖金**：全球赛 **$2,000**（🥇$1,000 / 🥈$500 / 🥉$300 / 4th $100 / 5th $100）
> **资格**：Free to join；**单人可报**（team 1–5）；官方页**无地域排除**；明确写 "No prior AI safety or epistemics background is required"。
> **Track 官方原文（Track 2 · Trust Infrastructure）**：*"What minimal tamper-evident layer is missing from today's AI observability standards, so that records of what agents did and agreed can be audited and trusted?"* —— 与 SwarmBox `chain.py` 逐字对应。

> 复用资产：本包与 Swarm Alignment 提交包（`SWARM_SUBMISSION.md`）共用同一个 `swarmbox` 仓库——**一鱼两吃**，同一份代码投两个 Apart 赛事的不同 Track，零额外开发成本。

---

## 一、报名（Sign up）表单字段 — 复制即填

入口：https://apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15 → **Sign up**（约 3 分钟，免费）

| 字段 | 填什么 |
|---|---|
| First name * | Yilang |
| Last name * | Zhi |
| Email * | 2383844705@qq.com |
| Location * | Shanghai, China |
| LinkedIn profile * | `N/A` |
| Google Scholar profile * | `N/A` |
| GitHub URL | `https://github.com/Zhiyilang` |
| Current job | RPA developer (UiBot / 影刀) transitioning into AI agent engineering; open to new roles. |
| Why are you joining? | I want to make tampering in multi-agent logs *visible at a specific index* rather than merely discouraged. |
| What project would you like to work on? | A minimal hash-chain layer on top of an existing append-only agent ledger, so a handed-over log can be checked offline for edit/delete/insert/reorder/truncation. |
| How did you hear about this Sprint? | Apart Research website |

---

## 二、提交（Submit your project）表单字段 — 复制即填

| 字段 | 填什么 | 必填 |
|---|---|---|
| Project title * | **SwarmBox — tamper-evident ledger layer** | ✅ |
| Project summary * | 见下方「摘要全文」 | ✅ |
| PDF report * | **`TRACK2.pdf`**（143,437 B，实测 `%PDF-1.4` + `/Type/Page` + `%%EOF`；9 节含 Limitations + Dual-Use 附录，4 页 ≤8 页） | ✅ |
| Are you interested in publishing this project? * | **Yes** | ✅ |
| Tracks | ☑ **Track 2: Trust Infrastructure** | ✅ |
| Project code | `https://github.com/Zhiyilang/swarmbox` ＋ `https://gitee.com/ZhiYIlang/swarmbox` | 推荐 |
| Project image | **`SWARM_COVER.png`**（1920×1080，121,592 B） | 推荐 |
| Slides | `SWARM_SLIDES.html`（浏览器打开 → 打印为 PDF） | 可选 |
| Presentation recording | 可选（非必填） | 可选 |
| Team name * | SwarmBox / Zhiyilang | ✅ |
| Location * | Shanghai, China | ✅ |
| Team member 1 Name * / Email * | Yilang Zhi / 2383844705@qq.com | ✅ |

### 摘要全文（Project summary，可直接粘）

> SwarmBox adds a minimal tamper-evident layer to an existing append-only multi-agent
> ledger. `chain.py` (118 lines, standard library only) adds two fields per record —
> `_prev` (digest of the prior record) and `_h` (digest of `(prev, canonical(record))`)
> — plus an externally published tail anchor. The result: integrity becomes
> *localisable*. A verifier does not merely learn "something is wrong"; it learns
> which index is wrong and which kind of wrong it is.
>
> `eval_chain.py` asserts **35 passed, 0 failed**. During the sprint (2026-11-14)
> we added `sprint2026_anchor.py` — **7 passed, 0 failed** — which *implements* the
> external tail-anchor mechanism and defeats truncation, forged-append and
> tampered-anchor attacks (repo total **277 passed, 0 failed**). Editing a field,
> deleting a record, duplicating one in place, swapping two adjacent records,
> stripping records from the head, and truncating/forging the tail are each detected,
> localised by index, and labelled with the failure mode. The same seed reproduces a
> byte-identical chained ledger and a stable tail digest.
>
> We state the boundary plainly: a hash chain does **not** detect silent tail
> truncation on its own — every record left in a truncated file still links up. We
> handle it the only way possible (an external tail anchor) and make both behaviours
> asserted tests, so the limit cannot silently regress into false confidence. This is
> integrity, not authenticity: we ship no signature or HMAC, and say so.

---

## 三、资产实测清单（宣称 = 实测，2026-10-31 00:3x 真跑）

| 资产 | 实测值 | 来源 |
|---|---|---|
| `eval.py` | **235 passed, 0 failed** | 实跑 |
| `eval_chain.py` | **35 passed, 0 failed**（子项：`[chain: round trip through disk]` / `[chain: primitives]` 均通过） | 实跑 |
| `sprint2026_anchor.py` | **7 passed, 0 failed**（2026-11-14 sprint 内新增：外部尾锚 + 伪造追加攻击检测） | 实跑 |
| 仓库合计 | **277 assertions, 0 failed** | 实跑 |
| `swarmbox/chain.py` | 118 行，stdlib only；`_prev` + `_h` + tail anchor；GitHub `Zhiyilang/swarmbox` 200 / Gitee `ZhiYIlang/swarmbox` 302（存在） | API 实测 |
| `TRACK2.pdf` | 143,437 B，`%PDF-1.4`、`/Type/Page`、`%%EOF` 有效；9 节含 Limitations + Dual-Use 附录，4 页 ≤8 页 | 字节校验 |
| 诚实边界 | 仅完整性非真实性；anchor 外部依赖；无 revocation/时间戳；单线程假设；证据基小（仅自测 testbed） | 文档声明 |

⚠️ **诚实声明（已写入 TRACK2 §5，提交不改口）**：本层证明「日志未被篡改」，但**不证明作者身份**（无签名/HMAC）；尾部截断检测依赖外部锚点；未在生产 agent 框架跑过。这些是原始设计的边界，不是缺陷。

---

## 四、卡点（按依赖序）

1. **Apart 报名（用户，~3 分钟）**：Sign up 后才有提交入口。
2. 提交前通读 `TRACK2.pdf` 确认最终版（平台提示 "Check it's the final version before you submit"）。
3. 与 Swarm Alignment 共用仓库，**两份提交互不影响**，可分别独立交。

---

> 官方规则源：apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15（2026-10-31 实抓，提交窗口将启）· 复用仓库 `swarmbox`（两端匿名可访问）
> **合规注记**：赛事要求「new work must be done during the sprint」。`chain.py`/`eval_chain.py`/`TRACK2.pdf` 初版为 10 月底 Swarm 资产；**2026-11-14 在窗口内新增 `sprint2026_anchor.py`（7 passed）+ TRACK2 §5 外部锚点章节 + §7 Dual-Use 附录**，确保提交含 sprint 期间新工作，非纯复用旧包。
