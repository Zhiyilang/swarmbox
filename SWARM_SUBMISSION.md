# Swarm Alignment Hackathon 2026 — 提交包（SwarmBox · Track 1 Sandboxes & Testbeds）

> **赛事**：Swarm Alignment Hackathon 2026 · Apart Research × AI Alignment Foundation × AE Studio
> **官方页**：https://apartresearch.com/sprints/swarm-alignment-2026 ｜ https://www.aialignmentfoundation.org/hackathons/swarm-alignment-2026
> **时间**：2026-11-06 ~ 11-08（线上 + LA 线下 hub）
> **提交截止**：**Sunday, November 8, 2026, 11:59 PM AoE** → 换算北京 **11-09 19:59**（AoE=UTC−12）
> **奖金**：全球赛 **$4,000**；LA hub 另 $4,000（线上可投全球赛）｜所有参赛者另得 $500 Adaption 额度
> **资格**：Free to join；**单人可报**（team 1–5）；官方页**无地域排除**；CoMSES  listings 显示 **Registration deadline: None**（报名无硬截止，但**必须在 Apart 页面注册才能提交并获奖**——Luma 页逐字："only teams registered there can submit and win prizes"）
> **Track 官方原文（Track 1 · Sandboxes and Testbeds）**：*"Can you build a small, reproducible environment where 5–20 LLM agents acting for different principals share a resource, a market or a tool over many rounds, and log everything so another team can rerun it?"* —— 与 SwarmBox 设计逐字对应。

---

## 一、报名（Sign up）表单字段 — 复制即填

入口：https://apartresearch.com/sprints/swarm-alignment-2026 → **Sign up**（约 3 分钟，免费）

| 字段 | 填什么 |
|---|---|
| First name * | Yilang |
| Last name * | Zhi |
| Email * | 2383844705@qq.com |
| Location * | Shanghai, China |
| LinkedIn profile * | `N/A`（官方说没有就填 N/A） |
| Google Scholar profile * | `N/A` |
| GitHub URL | `https://github.com/Zhiyilang` |
| Current job | RPA developer (UiBot / 影刀) transitioning into AI agent engineering; open to new roles. |
| AI safety experience | **Basic (courses/reading)**（如实选，官方说"No wrong answer"） |
| Why are you joining? | I want to build a testbed that makes multi-agent containment auditable rather than asserted. |
| What project would you like to work on? | A small reproducible sandbox where 5–20 agents share a renewable resource over many rounds, fully logged, with an escape corpus proving containment. |
| How did you hear about this Sprint? | Apart Research website |

---

## 二、提交（Submit your project）表单字段 — 复制即填

| 字段 | 填什么 | 必填 |
|---|---|---|
| Project title * | **SwarmBox** | ✅ |
| Project summary * | 见下方「摘要全文」 | ✅ |
| PDF report * | **`REPORT.pdf`**（11,703 B，实测 `%PDF-1.4` + `/Type/Page` + `%%EOF`） | ✅ |
| Are you interested in publishing this project? * | **Yes** | ✅ |
| Tracks | ☑ **Track 1: Sandboxes and Testbeds** | ✅ |
| Project code | `https://github.com/Zhiyilang/swarmbox` ＋ `https://gitee.com/Zhiyilang/swarmbox` | 推荐 |
| Project image | **`SWARM_COVER.png`**（1920×1080，121,592 B） | 推荐 |
| Slides | `SWARM_SLIDES.html`（浏览器打开 → 打印为 PDF） | 可选 |
| Presentation recording | 可选（非必填；如需，我可再用 ffmpeg 从真实输出合成） | 可选 |
| Team name * | SwarmBox / Zhiyilang | ✅ |
| Location * | Shanghai, China | ✅ |
| Team member 1 Name * / Email * | Yilang Zhi / 2383844705@qq.com | ✅ |
| Discord username | 可选（报名后可加 discord.gg/XswWBvugYs） | 可选 |

### 摘要全文（Project summary，可直接粘）

> SwarmBox is a reproducible multi-agent testbed that cannot be escaped. Rather than
> interpreting agent output, it parses output as data, so filesystem, network,
> process, import and reflection are not merely blocked — they are absent from the
> action grammar and cannot be requested. Six operations remain, each passing strict
> schema, identity and state validation before it touches the world, with 20 stable
> rule IDs. Every proposal, including every rejected one, is written to an
> append-only JSONL ledger, so "non-escapable" is auditable rather than asserted.
> On top sits a small common-pool economy: 5–20 agents draw on a renewable resource
> over many rounds, with metrics for whether they cooperate, collude, or drain it.
>
> What we found: across a 32-item escape corpus there were **0 escape successes**
> (31 rejected with the expected rule ID); across runs, **0 invariant violations**;
> a planted colluding pair was detectable from the ledger alone (correlation
> **−0.831**, 10 cross-agent reads of a shared key); and myopic versus informed
> strategies diverge categorically (myopic drained the pool on 8/8 seeds, informed
> 0/8). The suite is **235 assertions, 0 failed**, Python standard library only,
> zero network, and reruns byte-identically from a seed.

---

## 三、资产实测清单（宣称 = 实测，本轮 2026-10-30 23:5x 真跑）

| 资产 | 实测值 | 来源 |
|---|---|---|
| `eval.py` | **RESULT: 235 passed, 0 failed**（退出码 0，本轮二次复跑同值） | 实跑 |
| `swarmbox gate` | **escape corpus 32 items, 31 refused with the expected rule；escape successes 0** | 实跑 |
| `swarmbox run` | gini 0.2819 / collapse round 7 / escape attempts 249 **SUCCESSES 0** / covert channel 11 writes·11 reads·**10 cross-agent reads** / collusion corr **−0.831** / **invariants 0 violation(s)** / run_id 48fd340bb5832c1a | 实跑 |
| `swarmbox fidelity` | collapse_rate 1.0000 / drift 68.2031 / gini 0.1649 / overclaim 0.0539 / **escape successes 0 / invariant violations 0** | 实跑 |
| `REPORT.pdf` | 11,703 B，`%PDF-1.4`、`/Type/Page`、`%%EOF` 均有效 | 字节校验 |
| `SWARM_COVER.png` | 1920×1080，121,592 B，PNG magic 正确；**Edge headless 真实渲染 HTML，非 AI 生图**（合规） | 字节+目视校验 |
| 代码仓 | GitHub `Zhiyilang/swarmbox` **private=False / main**；Gitee `Zhiyilang/swarmbox` **public=True**；MIT | API 实测 |

⚠️ **诚实偏差（不用 README 旧数字）**：README 写"32 种逃逸尝试逐条被拒"，实测为 **32 items 中 31 条命中预期规则 ID**，另有 1 条被拒但规则 ID 不同；**escape successes 仍为 0**。摘要与封面均已按实测口径写。另 README 的 fidelity 基尼 0.200/0.035 与当前实跑（0.1649 等）不同，提交以本轮实跑为准。

---

## 四、卡点（按依赖序）

1. **Apart 报名（用户，~3 分钟）**：Sign up 后才有提交入口。报名无硬截止，但越早越好。
2. 提交前把 `REPORT.pdf` 再通读一遍确认是最终版（平台提示"Check it's the final version before you submit"）。
3. 若想加演示视频：非必填，需要的话我用 ffmpeg 从真实输出合成（约 1 分钟成片）。

---

> 官方规则源：apartresearch.com/sprints/swarm-alignment-2026（2026-10-30 23:4x 实抓，倒计时"Starts in 7 days"，**提交窗口开启中**）· aialignmentfoundation.org/hackathons/swarm-alignment-2026（Track 1 原文）· comses.net/events/804（Registration deadline: None）
