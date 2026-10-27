"""Append-only receipts.

Track 1 asks for a testbed "logged so another team can rerun it". A log that
only records what succeeded cannot support that: the interesting events are
the refusals. So every proposal is written **before** the gate decides, and
the verdict is appended to the same record. Nothing is dropped silently.

The ledger is JSONL and is the unit of reproducibility: a run is identified
by the sha256 of its ledger, and eval.py asserts that two runs with the same
seed produce byte-identical ledgers.
"""
import hashlib
import json
import os


def _dump(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


class Ledger:
    """Append-only receipts.

    ``chained=False`` (the default) reproduces the original byte-for-byte
    behaviour, including the ledger digests asserted by ``eval.py``.

    ``chained=True`` additionally embeds the previous record's digest into every
    record, so any later edit, deletion, insertion or truncation is detectable
    and localisable. See ``swarmbox/chain.py``.
    """

    def __init__(self, path=None, chained=False):
        self.path = path
        self.chained = chained
        self._rows = []
        self._tail = None
        if path and os.path.exists(path):
            os.remove(path)

    def _append(self, row):
        if self.chained:
            from .chain import GENESIS, FIELD_HASH, FIELD_PREV, row_digest

            prev = self._tail or GENESIS
            payload = dict(row)
            payload[FIELD_PREV] = prev
            payload[FIELD_HASH] = row_digest(prev, payload)
            self._tail = payload[FIELD_HASH]
            row = payload
        self._rows.append(row)
        if self.path:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(_dump(row) + "\n")

    # -- event types --------------------------------------------------
    def config(self, cfg):
        self._append({"t": "config", **cfg})

    def round_start(self, rnd, pool, held):
        self._append({"t": "round", "round": rnd, "pool": pool, "held": held})

    def proposal(self, rnd, agent, prop, ok, rule, reason, effect=None):
        row = {"t": "proposal", "round": rnd, "agent": agent, "op": prop.get("op"),
               "prop": prop, "decision": "allow" if ok else "refuse",
               "rule": rule, "reason": reason}
        if effect is not None:
            row["effect"] = effect
        self._append(row)

    def invariant(self, rnd, report):
        self._append({"t": "invariant", "round": rnd, **report})

    def summary(self, metrics):
        self._append({"t": "summary", "metrics": metrics})

    # -- reading ------------------------------------------------------
    @property
    def rows(self):
        return list(self._rows)

    def lines(self):
        return [_dump(r) for r in self._rows]

    def digest(self):
        h = hashlib.sha256()
        for line in self.lines():
            h.update(line.encode("utf-8"))
            h.update(b"\n")
        return h.hexdigest()

    def counts(self):
        """Decision counts, used by both the report and eval.py."""
        out = {"allow": 0, "refuse": 0, "by_rule": {}}
        for r in self._rows:
            if r.get("t") != "proposal":
                continue
            out[r["decision"]] += 1
            out["by_rule"][r["rule"]] = out["by_rule"].get(r["rule"], 0) + 1
        return out


def read_ledger(path):
    """Read a ledger, tolerating a truncated final line (killed writer)."""
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                # A torn last line is expected if the process was killed.
                # Anything earlier than the last line failing is real
                # corruption, so callers should check len(rows) > 0.
                continue
    return rows
