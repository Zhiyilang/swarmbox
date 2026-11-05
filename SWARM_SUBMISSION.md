# Swarm Alignment Hackathon 2026 — 提交包（SwarmBox · Track 1 Sandboxes & Testbeds）

> **赛事**：Swarm Alignment Hackathon 2026 · Apart Research × AI Alignment Foundation × AE Studio
> **官方页**：https://apartresearch.com/sprints/swarm-alignment-2026 ｜ https://www.aialignmentfoundation.org/hackathons/swarm-alignment-2026
> **时间（2026-11-06 00:3x 京核定）**：官方赛期 Friday 6 – Sunday 8 November 2026，**AoE = UTC−12**；换算北京为 **11-06 20:00 ~ 11-09 19:59**。Apart 页当时倒计时仍显示 "Starts in 0 days 22 hrs 37 min"，即北京 11-06 零点**尚未开赛**。
> **提交截止**：**Sunday, November 8, 2026, 11:59 PM AoE** → 北京 **11-09 19:59**
> **奖金**：全球赛 **$4,000**；LA hub 另 $4,000（线上可投全球赛）｜所有参赛者另得 $500 Adaption 额度
> **资格**：Free to join；**单人可报**（team 1–5）；官方页**无地域排除**；CoMSES  listings 显示 **Registration deadline: None**（报名无硬截止，但**必须在 Apart 页面注册才能提交并获奖**——Luma 页逐字："only teams registered there can submit and win prizes"）
> **Track 官方原文（Track 1 · Sandboxes and Testbeds）**：*"Can you build a small, reproducible environment where 5–20 LLM agents acting for different principals share a resource, a market or a tool over many rounds, and log everything so another team can rerun it?"* —— 与 SwarmBox 设计逐字对应。

---

## 一、报名（Sign up）表单字段 — 复制即填

入口：https://apartresearch.com/sprints/swarm-alignment-2026 → **Sign up**（约 3 分钟，免费）
> ✅ **本节仅作留档：报名已于 2026-11-05 完成，官方已发确认邮件，请勿再次提交表单。**

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
| PDF report * | **`REPORT.pdf`**（17,081 B / **6 页** / 222 词 Abstract；实测 `%PDF-1.4` + `%%EOF`） | ✅ |
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

### 摘要全文（Project summary / Abstract，可直接粘）

> **口径**：与 `REPORT.md` 的 Abstract 逐字一致，实测 **222 词**，落在官方要求的
> 150–250 词区间内。不要另写一份，避免表单与报告数字漂移。
>
> SwarmBox is a reproducible multi-agent testbed in which escape is not blocked but
> inexpressible. Agent output is parsed as data and never evaluated, so filesystem,
> network, process, import and reflection are absent from the action grammar and cannot
> be requested. Six operations remain; each passes strict schema, identity and state
> validation before it touches the world, and every proposal, including every refusal,
> is written to an append-only JSONL ledger with 20 stable rule identifiers.
> Conservation, non-negativity and capacity invariants are checked inside the world on
> every apply. On top of the gate sits a renewable common-pool economy in which 5 to 20
> deterministic agents draw over many rounds, with metrics for inequality, overclaim,
> drift, collapse and cross-agent coordination.
>
> We report four experiments. Across a 32-item adversarial corpus, 31 proposals are
> refused with the expected rule identifier, one legitimate self-referential proposal is
> allowed, and there are zero escape successes. Same-seed runs produce byte-identical
> ledger digests. A monitor reading only the ledger detects a planted colluding pair
> with correlation -1.000 and 11 cross-agent reads of a shared key, but the signal
> degrades once the resource collapses. Myopic policies drain the pool on 8 of 8 seeds
> while informed policies drain it on 0 of 8. The suite is 235 assertions, 0 failures,
> standard library only, zero network, and reruns byte-identically from a seed.

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

⚠️ **诚实偏差（不用 README 旧数字）**：`gate` 实测为 **32 items 中 31 条命中预期拒绝规则，另 1 条 `claim-own-name` 是合法自指请求、预期允许（R_OK）**；旧写法「32 条全被拒」和「另 1 条被拒但规则 ID 不同」均不准确，已按 `gate.py` 的 `ESCAPE_CORPUS` 源码逐条核对。**escape successes 仍为 0**。
⚠️ **E3 数字来源要标清**：报告与摘要用 `python -m swarmbox probe` 的口径（correlation **−1.000**、**11** cross-agent reads、planted detected True）；`python -m swarmbox run` 是另一套混合配置（correlation −0.831、10 cross-agent reads），两者都是实测但**不可混用**。README 的 fidelity 表与当前实跑一致（0.2003 / 0.0354 / 1.00 / 0.00）。

---

## 四、状态与剩余动作（2026-11-05 21:2x 更新）

**✅ 报名已完成，不需要再注册。** 官方 `AIAF Hackathon Team <hackathon@aialignmentfoundation.org>`
于 **2026-11-05 13:04 UTC（北京 21:04）** 发到 2383844705@qq.com 的确认邮件逐字：

> "Thanks for registering for the Swarm Alignment Hackathon, November 6–8, 2026.
> You signed up to take part online, in the global sprint."

（POP3 实读，UID 1150。）用户随后再次提交表单时看到「已用不同详细信息注册，未更改任何内容」
——这是**拒绝覆盖**，不是注册失败；原记录仍然有效，且系统明确"没有更改任何内容"。

已按页面指示从该邮箱发出英文更新信（`SENT ok`，主题 `Registration update -
2383844705@qq.com - Swarm Alignment Hackathon (Yilang Zhi)`）：把唯一记录统一为
Yilang Zhi / Shanghai, China / online global sprint / solo / Track 1，请官方忽略
第二次表单提交、确认注册有效，并问清提交入口与是否还有遗漏的资格步骤。留档
`.workbuddy/sent_mail/2026-11-05_swarm_registration_update.txt`。

**🟢 已无需用户动作**：报名已完成，交稿由自动化 `54bb3c9f` 于 **11-07 09:00（京）** 起自主执行（详见第六节）。下方表单仅作手动兜底留档。官方原文：

> "Where to submit: through the official submission form on the Sprint page."

**不要再用邮件交作品**（Collusion Sprint 已有 Kamil 两次明示只认官网按钮的教训）。
⚠️ **但别提前交**：官方 FAQ 逐字「The PDF itself is not replaced」——交了就不能改，且「only the weekend's work is judged」。建议 **11-06 开赛后**先补一个真实增量实验（新测量 / 新种子 / 新基线），写进报告独立「Weekend work」节、重建 PDF、双端同步后再一次性上传。当前 6 页 PDF 已满足全部硬性要求，若要立刻交也不会在资格上被卡。
提交后应收到含 project title 的确认邮件，项目 5 分钟内出现在官网；没有则写
`sprints@apartresearch.com`。Discord（官方确认邮件给的）：https://discord.gg/THWK7ZumW
—— 加入不是获奖硬条件，已在信中请官方确认。

## 五、官方 Guidelines 合规自检（2026-11-05 实抓 + 实测）

| 官方要求（Guidelines 原文） | 我们的状态 |
|---|---|
| "Research report (PDF) using the official template." | ⚠️ 见下方唯一未消除项 |
| "Maximum 8 pages, not counting references and appendices." | ✅ **6 页**（`REPORT.pdf` 实测 `/Type/Page` = 6） |
| "Project title and abstract, 150 to 250 words." | ✅ 标题 + **222 词** Abstract（脚本实测） |
| "Author names and affiliations." | ✅ Yilang Zhi / Independent researcher, Shanghai, China |
| "A 'Limitations and Dual-Use / Ethical Considerations' appendix (required)." | ✅ `REPORT.md` Appendix A，含双用途风险 4 条 + 缓解措施 |
| "Mark any code you wrote before the sprint as preexisting in the README and the report." | ✅ `README.md` / `README.zh.md` / `REPORT.md` Appendix B 三处声明 |
| "Only the weekend's work is judged… Every submission is screened for it." | ✅ 如实披露代码写于 10 月，不冒充周末成果 |
| "Optional: Public GitHub repo." | ✅ https://github.com/Zhiyilang/swarmbox （+ Gitee 镜像） |
| "Optional: A 3 to 5 minute video demo." | 可选，`swarmbox_demo.mp4` 79.03s 已就绪 |
| "Where to submit: through the official submission form on the Sprint page." | 🔴 待用户 11-06 后点表单 |
| "Submissions are due end of day Sunday November 8, 11:59 PM AoE" | 北京 **11-09 19:59** |

⚠️ **唯一未消除项**：官方模板是 Google Docs `/copy` 链接
（`docs.google.com/document/d/1_1_27EyZriMlc8n8EBE2YScaeyMjm-8xjR097nmHXAE/copy`），
需要 Google 账号且本机代理抓该域返回 502。`REPORT.pdf` 因此按 Guidelines 的
Recommended Report Structure 逐节排版，全部必需字段齐备。若用户能打开模板，可把
`REPORT.md` 内容粘进模板导出 PDF；否则直接交当前 PDF（结构合规，不是模板皮）。

## 六、自动化投递（2026-11-05 21:5x 设置，理论零用户动作）

| 项 | 值 |
|---|---|
| Automation ID | `54bb3c9f-ae36-4d2f-9a4b-6b418d994743`（由原「提交截止闸门」升级复用，未新建重复任务） |
| 首次运行 | **2026-11-07 09:00（京）**，之后每天 09:00 幂等复检至 11-09（末次距截止 19:59 尚有约 11h） |
| 规则 | `FREQ=DAILY;BYHOUR=9;BYMINUTE=0`；validFrom 11-07 / validUntil 11-09 |
| 开赛口径 | 北京 2026-11-06 20:00 = AoE 11-06 00:00；**首次执行已落在赛期内**，不抢跑 |

执行链（两个脚本均已写好并通过 dry-run / smoke 实测）：

1. `python _apart_submit.py --check` —— 已提交则立即停手（PDF 不可替换）。
2. `cd swarmbox && python weekend_increment.py --full` —— **合规时间闸门**：北京 11-06 20:00（= AoE 11-06 00:00）前 ABORT（11-06 00:41 实测 rc=2、报告一字节未改），杜绝把赛前数据写成「周末工作」；通过后实跑 5/8/12/16/20 agents × 8 seeds 规模扫描 → `WEEKEND_RESULTS.json` → 插入 `REPORT.md` 的 Appendix C → 重建 PDF → 同步 GitHub/Gitee。
3. `python eval.py` + `python _apart_submit.py --dry-run` 终检（235/0、LIVE 令牌、222 词、19 字段、Submit project 按钮、**`Data check: SAFE`**）。
4. `python _apart_submit.py --submit` —— 实时抓 Next.js Server Action 令牌，向官网表单 POST 一次；标记写 `.workbuddy/swarm_submit_attempted.json`，响应存 `.workbuddy/swarm_submit_response_*.html`。
5. `python _apart_submit.py --verify` —— 确认邮件 / 官网收录回验；失败**不重发 POST**，改推手动清单给用户。

表单实测（2026-11-05）：`multipart/form-data` POST 到 Sprint 页自身，**无登录、无验证码**，唯一 bot 闸门 `leave_blank` 留空；字段 19 个（注意 `ProjectSummary_Framer ` 带尾随空格）；4 个隐藏令牌必须实时抓取，提交时禁用缓存。

### 时间口径订正与一次赛前数据事故（2026-11-06 00:3x–00:4x 京）

初版把开赛当成「北京 11-06 00:00」，闸门和自动化分别设为 00:00 / 17:00。核官方页后确认赛期用 **AoE**，北京零点其实是 AoE 11-05，尚未开赛，抢跑约 20 小时。期间另一个进程在旧闸门下于 **00:35:46** 跑出了 `WEEKEND_RESULTS.json` 并写入本地 `REPORT.md` / `REPORT.pdf`，文中还声称 "Generated during the sprint window"。

处置（全部有回验）：

| 动作 | 结果 |
|---|---|
| 读双端公开仓库 | GitHub / Gitee 仍为干净的 17,818 B / 17,081 B，**未被污染**（该进程在 `validate()` 处抛异常退出，未执行同步） |
| 本地回滚 | 从 GitHub raw 覆盖 `REPORT.md` / `REPORT.pdf`，逐字节一致；赛前数据隔离到 `.workbuddy/quarantine_weekend_results_0005.json`，不参与提交 |
| 闸门订正 | 两个脚本 `SPRINT_START` 统一为北京 11-06 20:00；自动化改 11-07 09:00 首跑 |
| 根因修复 | `appendix_c()` 漏了 `## Appendix C` 标题（上一轮改格式化时误删），导致 `validate()` 的 weekend appendix 检查必然 FAIL、自动化会永远卡在第二步；已补回标题，并给 `patch_report()` 加无标题残留兜底清理 |
| 新增硬闸门 | `_apart_submit.py` 的 `report_data_is_sprint_safe()`：报告一旦声称周末工作，就校验 `WEEKEND_RESULTS.json` 的 `generated_at` 必须 ≥ 开赛时刻；否则 `--submit` 直接 ABORT。隔离测试 4/4 通过（干净版放行、赛前数据拦截、赛期内放行、缺结果文件拦截） |

⚠️ **诚实边界**：因「PDF 交了不能替换」，不能为了测试而提前真提交，所以**直连 POST 尚未经过一次真实成功验证**（dry-run 只构造不发送）。若到点 POST 返回 failed，脚本允许后续每日重试（官方 FAQ：同标题重交会更新记录，不创建重复项目）；若 11-09 仍失败，自动化会把手动清单推到本文件顶部并告知用户，届时仍需用户 3 分钟点一下。

**手动兜底清单（约 3 分钟）**：Apart Sprint 页 → Submit your project → 上传 `REPORT.pdf` → 粘第二节 222 词摘要 → 选 Track 1 → Yes publishing → Team `SwarmBox` / Location `Shanghai, China` / Name `Yilang Zhi` / Email `2383844705@qq.com` / Project code `https://github.com/Zhiyilang/swarmbox` → Submit project。提交后应收到确认邮件，项目 5 分钟内上官网。

---

> 官方规则源：aialignmentfoundation.org/hackathons/swarm-alignment-2026（2026-11-05 实抓：奖池 $4,000 明细 1st $2,000 / 2nd $1,000 / 3rd $600 / 4–5th $200；solo 可；"Global submissions due 23:59 AoE"）· apartresearch.com/sprints/swarm-alignment-2026#guidelines（2026-11-05 实抓：Submission Requirements / Recommended Report Structure / Important Notes / FAQ 全文）· 官方注册确认邮件 UID 1150（2026-11-05 13:04 UTC）
