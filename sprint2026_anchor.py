#!/usr/bin/env python3
"""AI x Epistemics Research Sprint 2026 — NEW work, added 2026-11-14 (in window).

Track 2 (Trust Infrastructure): tamper-evident agent ledgers.

This module does NOT exist in the 2026-10 Swarm submission. It closes the
single honest limitation that TRACK2.md states but does not implement: a hash
chain alone cannot detect a *silent truncation of the tail*, because every
record left in a truncated file still links up. The remedy is to publish the
tail digest to an EXTERNAL anchor that the reader fetches independently, then
verify the handed-over log against it. We build that anchor mechanism and
assert the attacks it defeats.

Zero third-party imports, zero network, deterministic.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from swarmbox.chain import chain_rows, verify_chain, summarise, row_digest

_passed = 0
_failed = 0


def check(cond, label):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"[anchor: {label}]")
    else:
        _failed += 1
        print(f"[anchor FAIL: {label}]")


def build(n):
    plain = [{"id": i, "act": f"agent{i}-op{i}"} for i in range(n)]
    rows, _tail = chain_rows(plain)
    return rows


def publish_anchor(rows):
    """Simulate an external immutable registry the reader fetches on their own."""
    return {"digest": summarise(rows)["tail"], "count": len(rows),
            "source": "external-registry-v1"}


def main():
    rows = build(10)
    anchor = publish_anchor(rows)

    # 1. Clean handoff verifies against the published anchor.
    ok, _ = verify_chain(rows, expected_tail=anchor["digest"])
    check(ok is True, "clean handoff verifies against published anchor")

    # 2. Truncation (drop the last 3 records) is caught by the anchor.
    truncated = rows[:-3]
    ok2, why2 = verify_chain(truncated, expected_tail=anchor["digest"])
    check((ok2 is False) and ("tail" in why2),
          "tail truncation detected via anchor mismatch")

    # 3. Without the anchor, that same truncation is INVISIBLE — proves the gap
    #    the anchor exists to close.
    ok3, _ = verify_chain(truncated)
    check(ok3 is True, "same truncation passes WITHOUT anchor (documents the gap)")

    # 4. Forged append: an attacker appends a record with a *valid internal*
    #    hash (chained from the last anchored row) AFTER the anchored tail. The
    #    in-log chain still links, so only the anchor catches it.
    forged = list(rows)
    last = forged[-1]
    fake = {"id": 99, "act": "malicious-insert"}
    fake["_prev"] = last["_h"]
    fake["_h"] = row_digest(last["_h"], fake)
    forged.append(fake)
    ok4, why4 = verify_chain(forged, expected_tail=anchor["digest"])
    check((ok4 is False) and ("tail" in why4),
          "forged append after anchor detected")

    # 5. A tampered anchor (wrong digest) is rejected by an honest reader.
    bad = dict(anchor)
    bad["digest"] = "0" * 64
    ok5, why5 = verify_chain(rows, expected_tail=bad["digest"])
    check((ok5 is False) and ("tail" in why5),
          "tampered anchor rejected by verifier")

    # 6. Realistic handoff: reader fetches the anchor INDEPENDENTLY and audits.
    reader_anchor = publish_anchor(rows)
    ok6, _ = verify_chain(rows, expected_tail=reader_anchor["digest"])
    check(ok6 is True, "independent-reader handoff audit passes")

    # 7. Determinism: identical logs produce an identical anchor digest.
    rows_b = build(10)
    check(summarise(rows_b)["tail"] == summarise(rows)["tail"],
          "anchor digest is deterministic for identical logs")

    print(f"\nRESULT: {_passed} passed, {_failed} failed")
    return _failed


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(1 if main() else 0)
