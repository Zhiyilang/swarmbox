"""Cheap vs frontier: how far can a stand-in go before results stop matching?

Track 1's last question is the one most worth answering honestly:

    "How far can a cheap model stand in for a frontier agent before the
    results stop matching?"

We answer it the only way we can without calling any model: run the *same*
world under two policy families that differ in what they can condition on,
over many seeds, and measure where the outcomes diverge.

  cheap family     sees its own holding and the pool only.
  frontier family  additionally sees the swarm's recent aggregate behaviour
                   and adapts (forecaster, adapter).

If the two families produce the same headline metrics, then for this
testbed a cheap stand-in is good enough and a team can save its budget. If
they diverge, we report on which metric and by how much - that is the
actual result, and it is the number a follow-up team should reuse.

We deliberately do not claim this measures real LLMs. It measures whether
the *information set* matters in this environment.
"""
from .agents import FAMILY, ROLES
from .swarm import (DEFAULT_AGENTS, DEFAULT_CAPACITY, DEFAULT_REGEN,
                    DEFAULT_ROUNDS, run)

CHEAP_ROLES = tuple(r for r in ROLES if FAMILY[r] == "cheap")
FRONTIER_ROLES = tuple(r for r in ROLES if FAMILY[r] == "frontier")


def _roles_for(n, family):
    """Deterministic role assignment drawn from one family (or mixed)."""
    if family == "cheap":
        pool = CHEAP_ROLES
    elif family == "frontier":
        pool = FRONTIER_ROLES
    elif family == "mixed":
        pool = ROLES
    else:
        raise ValueError("unknown family %r" % (family,))
    names = ["agent_%02d" % (i + 1) for i in range(n)]
    return {a: pool[i % len(pool)] for i, a in enumerate(names)}


def _mean(xs):
    return round(sum(xs) / len(xs), 6) if xs else 0.0


def aggregate(metrics_list):
    """Collapse several seeds into headline statistics."""
    ginis = [m["gini_holdings"] for m in metrics_list]
    over = [m["overclaim_mean"] for m in metrics_list]
    drifts = [m["drift"] for m in metrics_list]
    collapses = [1 if m["collapse_round"] is not None else 0
                 for m in metrics_list]
    return {
        "seeds": len(metrics_list),
        "gini_mean": _mean(ginis),
        "gini_spread": round(max(ginis) - min(ginis), 6) if ginis else 0.0,
        "overclaim_mean": _mean(over),
        "drift_mean": _mean(drifts),
        "collapse_rate": _mean(collapses),
        "escape_successes": sum(m["escape"]["successes"] for m in metrics_list),
        "invariant_violations": sum(len(m["invariant_violations"])
                                    for m in metrics_list),
    }


def compare(n=DEFAULT_AGENTS, rounds=DEFAULT_ROUNDS,
            seeds=(1, 2, 3, 4, 5, 6, 7, 8),
            capacity=DEFAULT_CAPACITY, regen=DEFAULT_REGEN):
    """Run cheap / frontier / mixed populations and measure the gap."""
    families = {}
    for fam in ("cheap", "frontier", "mixed"):
        runs = []
        for s in seeds:
            res = run(n=n, rounds=rounds, seed=s, capacity=capacity,
                      regen=regen, roles=_roles_for(n, fam))
            runs.append(res.metrics())
        families[fam] = aggregate(runs)

    def gap(key):
        return round(abs(families["cheap"][key] - families["frontier"][key]), 6)

    return {
        "config": {"n": n, "rounds": rounds, "seeds": len(seeds),
                   "capacity": capacity, "regen": regen},
        "families": families,
        "divergence": {
            "gini": gap("gini_mean"),
            "overclaim": gap("overclaim_mean"),
            "drift": gap("drift_mean"),
            "collapse_rate": gap("collapse_rate"),
        },
    }
