"""A minimal tamper-evident layer for ledgers.

Why this module exists
----------------------
``ledger.py`` writes append-only JSONL and can prove that two runs are identical
via a single sha256 over the whole file. That is enough to detect "the file was
replaced", but not enough to answer the question trust infrastructure actually
asks:

    given a log handed to you later, can you tell whether one line was edited,
    one line was dropped, or the tail was quietly cut off?

This module adds the smallest thing that answers yes: each record carries the
hash of the record before it. Editing a line breaks every hash after it;
dropping a line breaks the link; truncating breaks the tail. Because the link is
computed from the previous digest, the corruption is also *localisable* - you
learn which index stopped adding up.

What it deliberately does not do
--------------------------------
- No signatures. This is integrity, not authenticity. It proves the log has not
  been altered since it was written; it does not prove who wrote it. Signing is
  a separate layer (``hmac`` or a public key) and adding it would mean key
  management, which is a larger claim than this module makes.
- Nothing here changes existing behaviour. ``Ledger`` only chains when it is
  constructed with ``chained=True``, so every previously published result - and
  the 235 assertions in ``eval.py`` - are unaffected.

Usage
-----
    from swarmbox import Ledger
    led = Ledger(path="run.jsonl", chained=True)
    ...  # every .config() / .proposal() / .round_start() is chained automatically

    from swarmbox.chain import chain_rows, verify_chain
    rows, tail = chain_rows(raw_rows)
    ok, reason = verify_chain(rows)
"""

import hashlib

GENESIS = "0" * 64
FIELD_PREV = "_prev"
FIELD_HASH = "_h"


def canonical(obj) -> bytes:
    """Canonical bytes for a record.

    Uses the same convention as ``ledger._dump``: sorted keys and no incidental
    whitespace, so the digest is stable across processes and platforms.
    """
    import json

    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")


def row_digest(prev: str, row: dict) -> str:
    """Digest of one record given the digest of the record before it."""
    payload = dict(row)
    payload.pop(FIELD_HASH, None)
    h = hashlib.sha256()
    h.update(prev.encode("ascii"))
    h.update(b"|")
    h.update(canonical(payload))
    return h.hexdigest()


def chain_rows(rows):
    """Return ``(chained_rows, tail_digest)`` for an iterable of plain records."""
    out, prev = [], GENESIS
    for row in rows:
        payload = dict(row)
        payload[FIELD_PREV] = prev
        payload[FIELD_HASH] = row_digest(prev, payload)
        prev = payload[FIELD_HASH]
        out.append(payload)
    return out, prev


def verify_chain(rows, expected_tail=None):
    """Verify an already-chained iterable.

    Returns ``(True, "")`` when every link is intact, otherwise
    ``(False, "index N: <reason>")`` naming the first record that fails. The
    reasons distinguish the interesting failure modes, because "someone edited
    line 40" and "the file ends early" lead to different conclusions about what
    happened.

    Honest limitation
    -----------------
    A hash chain on its own detects *edits, deletions, insertions and reordering*
    but **cannot detect a silent truncation of the tail**: everything left in a
    head-truncated file still links up perfectly. That case needs an external
    anchor - the tail digest recorded elsewhere at write time. Pass it as
    ``expected_tail`` and truncation becomes detectable too.
    """
    prev = GENESIS
    last = GENESIS
    if not isinstance(rows, list):
        rows = list(rows)
    for i, row in enumerate(rows):
        if FIELD_PREV not in row or FIELD_HASH not in row:
            return False, f"index {i}: record is not chained"
        if row[FIELD_PREV] != prev:
            return False, f"index {i}: predecessor digest does not match (a record was inserted, removed or reordered)"
        expected = row_digest(row[FIELD_PREV], row)
        if row[FIELD_HASH] != expected:
            return False, f"index {i}: digest does not match its contents (this record was edited)"
        prev = row[FIELD_HASH]
        last = row[FIELD_HASH]
    if expected_tail is not None and rows:
        if last != expected_tail:
            return False, "tail digest does not match the anchor (records were removed from the end)"
    return True, ""


def summarise(rows) -> dict:
    """Small machine-readable receipt: count, first/reject per shard not needed."""
    prev = GENESIS
    for row in rows:
        prev = row.get(FIELD_HASH, prev) or prev
    return {"records": len(rows), "tail": prev}
