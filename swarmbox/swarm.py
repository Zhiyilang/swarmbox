"""The round loop: deterministic, gated, fully receipted.

Reproducibility contract (this is what "another team can rerun it" means
here): a run is a pure function of (seed, n, rounds, capacity, regen, roles).
Same inputs in, byte-identical ledger out. eval.py asserts that by running
the same configuration twice and comparing digests.
"""
import random

from . import agents as _agents
from . import metrics as _metrics
from .gate import MAX_PROPOSALS, R_ROUND_LIMIT, screen
from .ledger import Ledger
from .world import World

# Defaults are calibrated, not arbitrary. At (12 agents, capacity 1200,
# regen 300) the difference between the myopic and informed policy families
# is at its widest while both still produce live dynamics for the whole run:
# the myopic family exhausts the pool, the informed family never does. See
# the "Parameter calibration" section of REPORT.md before changing these.
DEFAULT_AGENTS = 12
DEFAULT_ROUNDS = 24
DEFAULT_CAPACITY = 1200
DEFAULT_REGEN = 300


class RunResult:
    def __init__(self, seed, world, rounds, ledger, claims_by_round, pool_series,
                 roles, run_id):
        self.seed = seed
        self.world = world
        self.rounds = rounds
        self.ledger = ledger
        self.claims_by_round = claims_by_round
        self.pool_series = pool_series
        self.roles = roles
        self.run_id = run_id

    @property
    def frontier_fraction(self):
        return _agents.family_mix(list(self.roles.values()))

    def claims_by_agent(self):
        """agent -> per-round claim series, in round order."""
        out = {a: [] for a in self.world.agents}
        for r in sorted(self.claims_by_round):
            for a in self.world.agents:
                out[a].append(self.claims_by_round[r].get(a, 0))
        return out

    def metrics(self):
        return _metrics.summarize(self)


def run(n=12, rounds=DEFAULT_ROUNDS, seed=7, capacity=DEFAULT_CAPACITY,
        regen=DEFAULT_REGEN, roles=None, ledger_path=None,
        ledger_chained=False):
    """Run one swarm experiment. Returns a RunResult.

    ``ledger_chained=True`` writes the receipts with the tamper-evident chain
    from ``swarmbox/chain.py``. It is off by default so published results and
    their digests stay unchanged.
    """
    names, default_roles = _agents.make_population(n)
    if roles is None:
        roles = dict(zip(names, default_roles))
    else:
        roles = dict(roles)
        names = [a for a in names if a in roles] or sorted(roles)
    missing = [a for a in names if a not in roles]
    if missing:
        raise ValueError("agents without a role: %s" % ",".join(missing))

    world = World(names, capacity=capacity, regen=regen)
    led = Ledger(ledger_path, chained=ledger_chained)
    cfg = {"seed": seed, "agents": len(names), "rounds": rounds,
           "capacity": capacity, "regen": regen,
           "roles": {a: roles[a] for a in sorted(roles)}}
    led.config(cfg)

    rng = random.Random(seed)
    claims_by_round = {}
    pool_series = []
    last_overclaim = None

    for rnd in range(1, rounds + 1):
        world.round = rnd
        world.inject()
        led.round_start(rnd, world.pool, world.total_held())
        claims_by_round[rnd] = {a: 0 for a in names}

        # Deterministic turn order: same seed -> same order, every time.
        order = list(names)
        rng.shuffle(order)

        for agent in order:
            view = {
                "round": rnd,
                "pool": world.pool,
                "holding": world.holding(agent),
                "fair_share": world.fair_share(),
                "n_agents": len(names),
                "regen": regen,
                "capacity": capacity,
                "last_overclaim": last_overclaim,
                "inbox": world.inbox[agent],
            }
            try:
                proposals = _agents.propose(roles[agent], agent, view)
            except Exception as exc:                     # policy bug is data
                led.proposal(rnd, agent, {"op": "?", "error": str(exc)},
                             False, "policy.error", str(exc))
                continue
            if not isinstance(proposals, list):
                proposals = [proposals]
            for idx, prop in enumerate(proposals):
                if idx >= MAX_PROPOSALS:
                    led.proposal(rnd, agent, prop, False, R_ROUND_LIMIT,
                                 "more than %d proposals in one round" % MAX_PROPOSALS)
                    continue
                ok, rule, why = screen(prop, world, agent)
                effect = None
                if ok:
                    try:
                        effect = world.apply(prop, agent)
                    except Exception as exc:
                        ok, rule, why = False, "world.rejected", str(exc)
                led.proposal(rnd, agent, prop, ok, rule, why, effect)
                if ok and prop.get("op") == "claim":
                    claims_by_round[rnd][agent] += prop["amount"]

        led.invariant(rnd, world.invariant_report())
        pool_series.append(world.pool)
        last_overclaim = sum(claims_by_round[rnd].values()) / float(regen) if regen else 0.0

    result = RunResult(seed, world, rounds, led, claims_by_round, pool_series,
                       roles, "")
    led.summary(result.metrics())
    result.run_id = led.digest()
    return result
