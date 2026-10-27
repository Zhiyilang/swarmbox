"""SwarmBox - an inescapable, reproducible multi-agent testbed.

Built for the Swarm Alignment Hackathon 2026, Track 1 (Sandboxes & testbeds).

The one-sentence claim: **agents in this box cannot leave it, and we can show
you the receipts.**

Two ideas carry that claim.

1. *The sandbox is not an interpreter.* Agent output is parsed as data and
   never evaluated. Filesystem, network, subprocess, import and reflection
   are not blocked - they are absent from the grammar, so they cannot be
   requested. What is left is six operations, each schema-checked and
   resource-checked by ``gate.py`` before it touches the world.

2. *Refusals are first-class receipts.* Every proposal is logged before the
   gate decides, and the verdict is attached to the same record. A log of
   only-successful actions could not support any containment claim.

Track 1 also asks how far a cheap model can stand in for a frontier one.
That question is answered by ``fidelity.py``: run the same swarm under a
myopic policy family and under an informed one, and measure where the
results stop matching.

Nothing here imports a third-party package and nothing here opens a socket.
"""
from .agents import FAMILY, ROLES, family_mix, make_population, propose
from .gate import (ESCAPE_CORPUS, MAX_AMOUNT, MAX_PROPOSALS, OPS, R_OK,
                   check_shape, check_state, screen)
from .ledger import Ledger, read_ledger
from .metrics import (channel_report, collusion_report, collapse_round, drift,
                      escape_report, gini, overclaim_series, pearson, summarize)
from .swarm import RunResult, run
from .world import InvariantError, World

__version__ = "0.1.0"
RELEASE_AUTHORITY = "deterministic-verifier"
