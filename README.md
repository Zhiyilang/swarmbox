# SwarmBox

**An inescapable, reproducible multi-agent testbed.**
Built for the Swarm Alignment Hackathon 2026, Track 1 (Sandboxes & testbeds).

> Agents in this box cannot leave it — and we can show you the receipts.

Full write-up: **[REPORT.md](REPORT.md)**. This file is the operator's manual.

## The idea in one paragraph

The sandbox is **not an interpreter**. Agent output is parsed as data and never
evaluated, so filesystem, network, subprocess, import and reflection are not blocked —
they are absent from the grammar and cannot be requested. What is left is six
operations, each schema-checked and resource-checked before it touches the world. Every
proposal, including every refusal, is written to an append-only ledger, so a containment
claim can be audited instead of believed. On top of that sits a small common-pool
economy: 5–20 agents draw on a regenerating resource over many rounds, and the metrics
say whether they cooperate, collude, or eat it empty.

## Quick start

```bash
python eval.py              # 235 assertions, 0 failures (includes the attack corpus)
python -m swarmbox gate     # 32 escape attempts, each refused with its rule id
python -m swarmbox run      # one mixed swarm
python -m swarmbox probe    # planted collusion pair, seen from the ledger only
python -m swarmbox fidelity # cheap vs frontier, 8 seeds
```

Python 3.9+. **Zero third-party packages, zero network.** `git clone && python eval.py`
is the whole setup.

## What you get

```
python -m swarmbox run
  run_id            b8fe9194f16653be
  agents / rounds   12 / 24   (seed 7)
  gini holdings     0.2819
  collapse round    7
  escape attempts   249  refused 0  applied 249  SUCCESSES 0
  collusion pair    agent_07 <-> agent_08  corr -0.831
  invariants        0 violation(s)
```

```
python -m swarmbox fidelity
  family           gini  overclaim      drift   collapse
  cheap          0.2003      1.125   -112.500       1.00
  frontier       0.0354      1.071    -44.297       0.00
  mixed          0.2638      1.152   -104.672       1.00
```

The headline: **the myopic family exhausts the pool on all 8 seeds; the informed family
never does.** See REPORT.md §3 E4 before quoting this.

## Architecture

```
agent policy ──▶ proposals ──▶ GATE ──▶ world ──▶ ledger (append-only JSONL)
                                 │                    │
                    shape / identity / state      metrics, reruns,
                    every refusal recorded       the audit trail
```

| Module | Role |
|---|---|
| `gate.py` | Six operations, strict schema, 20 stable rule ids, 32-item attack corpus |
| `world.py` | Common-pool resource, private cells, shared scratch, invariants |
| `agents.py` | 8 deterministic policies in two families (cheap / frontier) |
| `swarm.py` | Round loop; a run is a pure function of its config |
| `ledger.py` | Append-only JSONL; refusals are first-class records |
| `metrics.py` | Gini, overclaim, drift, collapse, correlation, covert-channel count |
| `fidelity.py` | The cheap-vs-frontier experiment |
| `probe.py` | The planted-collusion experiment |

## Containment, in three layers

| Layer | Stops |
|---|---|
| Structural (not in the grammar) | filesystem, network, process, import, reflection |
| Schema (strict, no unknown fields) | smuggling, type confusion, impersonation |
| State (checked against the world) | over-claim, over-release, reserved namespaces |

Invariants re-checked after every single `apply()`:

```
pool + total_extracted == injected     pool >= 0     every holding >= 0     pool <= capacity
```

An agent that escapes would have to conjure units from nothing. Arithmetic is the
tripwire; the gate is the fence.

## Reproducibility

A run is a pure function of `(seed, n, rounds, capacity, regen, roles)`. Same inputs →
byte-identical ledger digest, every time (asserted for seeds 1–5 in `eval.py`). The
ledger's first line records the full configuration, so a team handed only the ledger
knows exactly what to rerun.

## Honesty section

Things this project does **not** claim:

* **No language model is called anywhere.** All eight policies are pure functions. The
  cheap/frontier result is about *information sets*, not a benchmark of real models.
* **Escapes are refused within the action language.** We argue the language cannot
  express an escape. We are not a general-purpose code-execution sandbox and do not
  claim to defeat one.
* **The gate is static analysis, not a runtime sandbox.** It holds because SwarmBox
  offers no path to the host, not because it withstands a determined runtime attack.
* **Collusion detection here is correlation-based.** It catches turn-taking. It would
  not catch sophisticated collusion.

## License

MIT. See [LICENSE](LICENSE).
