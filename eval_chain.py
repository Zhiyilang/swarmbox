#!/usr/bin/env python3
"""Assertions for the tamper-evident ledger layer (swarmbox/chain.py).

Run standalone:  python3 eval_chain.py
Run together:    python3 eval.py && python3 eval_chain.py

This suite exists because "our log is append-only" is not a security claim. It
is a statement about the writer, and it cannot be checked by anyone who receives
the file later. Each test below attaches to a specific way a hostile party would
alter a handed-over ledger - edit, delete, insert, reorder, truncate - and
asserts what the verifier does about it, including the one case a hash chain
genuinely cannot cover on its own.

Zero third-party imports, zero network, deterministic.
"""
import copy
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from swarmbox import Ledger, run                                    # noqa: E402
from swarmbox.chain import (GENESIS, FIELD_HASH, FIELD_PREV,        # noqa: E402
                            chain_rows, row_digest, summarise,
                            verify_chain)

# --- tiny harness (same shape as eval.py) -----------------------------------
_passed = 0
_failed = 0


def _w(s=""):
    sys.stdout.write(s + "\n")


def check(cond, label):
    global _passed, _failed
    if cond:
        _passed += 1
    else:
        _failed += 1
        _w("  FAIL: " + label)


def section(name):
    _w("[chain: %s]" % name)


# --- 1. default behaviour is untouched -------------------------------------
_w()
section("backwards compatibility")
plain = run(n=5, rounds=3, seed=11)
rows_plain = plain.ledger.rows
check(len(rows_plain) > 0, "the unchained ledger still records events")
check(all(FIELD_PREV not in r for r in rows_plain),
      "default runs carry no %s field" % FIELD_PREV)
check(all(FIELD_HASH not in r for r in rows_plain),
      "default runs carry no %s field" % FIELD_HASH)
check(len(plain.ledger.digest()) == 64,
      "the whole-file digest is still a sha256 hex string")

# --- 2. a chained run is well formed ---------------------------------------
section("chained construction")
chained = run(n=5, rounds=3, seed=11, ledger_chained=True)
rows_ok = chained.ledger.rows
check(len(rows_ok) == len(rows_plain),
      "chaining records the same number of events as a plain run")
check(all(FIELD_PREV in r and FIELD_HASH in r for r in rows_ok),
      "every record carries both link fields")
check(rows_ok[0][FIELD_PREV] == GENESIS,
      "the first record links to the genesis digest")
check(len(GENESIS) == 64, "genesis is a 64-hex string")
ok, why = verify_chain(rows_ok)
check(ok, "an untouched chain verifies clean (%s)" % why)

# --- 3. both shapes still agree on the world -------------------------------
section("chaining does not change the experiment")
check(plain.metrics()["gini_holdings"] == chained.metrics()["gini_holdings"],
      "metrics are identical with and without chaining")

# --- 4. the attacks --------------------------------------------------------
section("tamper detection")
tam = copy.deepcopy(rows_ok)
mid = len(tam) // 2
tam[mid]["round"] = 99999
ok_edit, why_edit = verify_chain(tam)
check(not ok_edit, "editing a field in the middle is caught")
check("edited" in why_edit, "the edit failure names the reason")
check("index %d" % mid in why_edit, "the edit failure localises the index")

tam = copy.deepcopy(rows_ok)
del tam[mid]
ok_del, why_del = verify_chain(tam)
check(not ok_del, "deleting a record is caught")
check("predecessor" in why_del, "the deletion failure names the reason")

tam = copy.deepcopy(rows_ok)
tam.insert(mid, dict(tam[mid]))
ok_ins, _ = verify_chain(tam)
check(not ok_ins, "duplicating a record in place is caught")

tam = copy.deepcopy(rows_ok)
if len(tam) > 3:
    tam[1], tam[2] = tam[2], tam[1]
    ok_swap, _ = verify_chain(tam)
    check(not ok_swap, "swapping two adjacent records is caught")
else:
    check(False, "run produced too few records to test reordering")

tam = copy.deepcopy(rows_ok)
drop = dict(tam[0])
del tam[0]
ok_head, _ = verify_chain(tam)
check(not ok_head, "stripping records from the head is caught")
check(drop[FIELD_PREV] == GENESIS, "the removed head was the genesis record")

# --- 5. the honest limitation ----------------------------------------------
section("truncation: the boundary")
tail_anchor = summarise(rows_ok)["tail"]
check(len(tail_anchor) == 64, "the anchor is a 64-hex tail digest")

trunc = rows_ok[:max(1, len(rows_ok) - 2)]
ok_bare, _ = verify_chain(trunc)
check(ok_bare,
      "a tail-truncated chain STILL verifies with no anchor (documented limit)")
ok_anchored, why_anchored = verify_chain(trunc, expected_tail=tail_anchor)
check(not ok_anchored, "the same truncation is caught once an anchor is given")
check("tail" in why_anchored, "the truncation failure names the reason")

ok_full, _ = verify_chain(rows_ok, expected_tail=tail_anchor)
check(ok_full, "the complete chain still verifies against its own anchor")

# --- 6. determinism holds under chaining -----------------------------------
section("determinism under chaining")
a = run(n=6, rounds=4, seed=5, ledger_chained=True)
b = run(n=6, rounds=4, seed=5, ledger_chained=True)
check(a.run_id == b.run_id, "same seed reproduces a byte-identical chained ledger")
check(summarise(a.ledger.rows)["tail"] == summarise(b.ledger.rows)["tail"],
      "the chained tail digest is stable across runs")
c = run(n=6, rounds=4, seed=6, ledger_chained=True)
check(summarise(a.ledger.rows)["tail"] != summarise(c.ledger.rows)["tail"],
      "a different seed yields a different tail")

# --- 7. round trip through disk --------------------------------------------
section("round trip through disk")
tmp = os.path.join(tempfile.gettempdir(), "swarmbox_chain_eval.jsonl")
if os.path.exists(tmp):
    os.remove(tmp)
d = run(n=6, rounds=4, seed=7, ledger_path=tmp, ledger_chained=True)
check(os.path.exists(tmp), "a chained ledger file is written")
disk = []
with open(tmp, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line:
            disk.append(json.loads(line))
check(len(disk) == len(d.ledger.rows), "every chained record survives to disk")
ok_disk, why_disk = verify_chain(disk, expected_tail=summarise(d.ledger.rows)["tail"])
check(ok_disk, "the ledger read back from disk verifies (%s)" % why_disk)

# --- 8. primitives ---------------------------------------------------------
section("primitives")
check(row_digest(GENESIS, {"a": 1}) == row_digest(GENESIS, {"a": 1}),
      "row_digest is deterministic")
check(row_digest(GENESIS, {"a": 1}) != row_digest(GENESIS, {"a": 2}),
      "row_digest separates different payloads")
check(row_digest(GENESIS, {"b": 1, "a": 1}) == row_digest(GENESIS, {"a": 1, "b": 1}),
      "row_digest does not depend on key order")
r2, tail2 = chain_rows([{"x": 1}, {"x": 2}, {"x": 3}])
ok2, _ = verify_chain(r2, expected_tail=tail2)
check(ok2, "chain_rows + verify_chain round trip")
check(len(set(row_digest(GENESIS, {"x": i}) for i in range(8))) == 8,
      "row_digest has no collisions over a small sample")

_w()
_w("RESULT: %d passed, %d failed" % (_passed, _failed))
sys.exit(1 if _failed else 0)
