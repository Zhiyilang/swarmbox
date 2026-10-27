"""The Gate - the only path from an agent's intent to the shared world.

Containment claim (this is the whole point of Track 1):

    The sandbox is not an interpreter.

Agent output is parsed as *data* and is never evaluated. There is no
filesystem path, no socket, no subprocess, no import and no reflection
anywhere in the action grammar, so those escapes are not "blocked" -
they are inexpressible. What remains is a finite action language with six
operations, and every proposal is checked against the rules below before
it can touch the world.

Two-stage check, because the two stages fail for different reasons:

  * ``check_shape``  - pure structural validation, no world state needed.
  * ``check_state``  - resource / permission validation against the world.

A refused proposal is still written to the ledger. Silently dropping an
attack would make the ledger worthless as evidence.

Every rule has a stable id so a report can cite it.
"""
import re
import unicodedata

# ------------------------------------------------------------------
# the closed action language
# ------------------------------------------------------------------

OPS = ("claim", "release", "write", "read", "message", "spawn")

# Bounds. These are part of the containment story, not tuning knobs: an
# unbounded field is an unbounded attack surface.
MAX_AMOUNT = 64
MAX_PROPOSALS = 8
MAX_KEY_LEN = 64
MAX_VALUE_LEN = 256
MAX_BODY_LEN = 256

KEY_RE = re.compile(r"^[a-z0-9_]{1,64}$")

# Namespace prefixes agents may never touch, whatever the rest of the
# proposal looks like.
RESERVED_PREFIXES = ("private", "system", "gate", "ledger", "world")

# Schema per op: field -> allowed python type. Anything not listed is
# refused (strict schema: no smuggling data through unknown fields).
SCHEMA = {
    "claim": {"amount": int},
    "release": {"amount": int},
    "write": {"key": str, "value": str},
    "read": {"key": str},
    "message": {"to": str, "body": str},
    "spawn": {"role": str},
}

# Rule ids -> stable strings used in receipts and in the report.
R_OK = "ok"
R_UNKNOWN_OP = "gate.op.unknown"
R_BAD_TYPE = "gate.type.invalid"
R_BAD_AMOUNT = "gate.amount.invalid"
R_OVER_CAP = "gate.amount.over-cap"
R_BAD_KEY = "gate.key.invalid"
R_RESERVED_KEY = "gate.key.reserved"
R_CONTROL_CHAR = "gate.string.control-char"
R_NON_CANONICAL = "gate.string.non-canonical"
R_TOO_LONG = "gate.string.too-long"
R_UNKNOWN_FIELD = "gate.field.unknown"
R_MISSING_FIELD = "gate.field.missing"
R_IMPERSONATION = "gate.identity.impersonation"
R_OVER_POOL = "gate.pool.exhausted"
R_OVER_HOLDING = "gate.holding.insufficient"
R_UNKNOWN_PEER = "gate.message.unknown-peer"
R_NO_SPAWN_BUDGET = "gate.spawn.no-budget"
R_UNKNOWN_ROLE = "gate.spawn.unknown-role"
R_ROUND_LIMIT = "gate.round.too-many"


def _is_int(v):
    """True for int only. bool is a subclass of int and is refused."""
    return isinstance(v, int) and not isinstance(v, bool)


def _has_control(s):
    return any(ord(c) < 32 or ord(c) == 127 for c in s)


def _canonical(s):
    return unicodedata.normalize("NFKC", s) == s


def check_shape(prop):
    """Structure-only validation. Returns (ok, rule, reason).

    ``prop`` must be a dict. Anything else is refused rather than raising,
    because the proposal came from an untrusted agent.
    """
    if not isinstance(prop, dict):
        return False, R_BAD_TYPE, "proposal is not an object"

    # Identity first: a proposal may never name an agent other than the
    # one that submitted it. Impersonation is checked against the caller.
    for k in prop:
        if not isinstance(k, str):
            return False, R_BAD_TYPE, "non-string field name"

    op = prop.get("op")
    if not isinstance(op, str):
        return False, R_UNKNOWN_OP, "missing or non-string op"
    if op not in OPS:
        return False, R_UNKNOWN_OP, "op %r is not in the action language" % (op,)

    allowed = SCHEMA[op]
    for key, want in allowed.items():
        if key not in prop:
            return False, R_MISSING_FIELD, "op %s requires field %s" % (op, key)
        val = prop[key]
        if want is int:
            if not _is_int(val):
                return False, R_BAD_TYPE, "%s must be an integer" % key
        elif want is str:
            if not isinstance(val, str):
                return False, R_BAD_TYPE, "%s must be a string" % key

    # Strict schema: reject unknown fields outright. "agent" is the one
    # optional field - it is permitted here so that an impersonation
    # attempt is caught by the identity rule rather than by the schema,
    # which is what makes the refusal legible in the ledger.
    known = set(allowed) | {"op", "agent"}
    extra = sorted(set(prop) - known)
    if extra:
        return False, R_UNKNOWN_FIELD, "unexpected field(s) %s" % ",".join(extra)
    if "agent" in prop and not isinstance(prop["agent"], str):
        return False, R_BAD_TYPE, "agent must be a string"

    # String hygiene, applied to every string field the op carries.
    for key in allowed:
        if allowed[key] is not str:
            continue
        val = prop[key]
        if _has_control(val):
            return False, R_CONTROL_CHAR, "%s contains a control character" % key
        if not _canonical(val):
            return False, R_NON_CANONICAL, "%s is not NFKC-canonical" % key
        if key == "key" and len(val) > MAX_KEY_LEN:
            return False, R_TOO_LONG, "key exceeds %d chars" % MAX_KEY_LEN
        if key in ("value", "body") and len(val) > MAX_VALUE_LEN:
            return False, R_TOO_LONG, "%s exceeds %d chars" % (key, MAX_VALUE_LEN)

    # Op-specific structure.
    if op in ("claim", "release"):
        amt = prop["amount"]
        if amt <= 0:
            return False, R_BAD_AMOUNT, "amount must be positive (got %d)" % amt
        if amt > MAX_AMOUNT:
            return False, R_OVER_CAP, "amount %d exceeds per-proposal cap %d" % (
                amt, MAX_AMOUNT)
    if op in ("write", "read"):
        key = prop["key"]
        if not KEY_RE.match(key):
            return False, R_BAD_KEY, "key %r fails the namespace grammar" % (key,)
        if key.split("_")[0] in RESERVED_PREFIXES:
            return False, R_RESERVED_KEY, "key %r targets a reserved namespace" % (key,)
    if op == "message":
        if len(prop["body"]) > MAX_BODY_LEN:
            return False, R_TOO_LONG, "body exceeds %d chars" % MAX_BODY_LEN
    return True, R_OK, "shape ok"


def check_identity(prop, agent_id):
    """A proposal may carry no identity field at all; if it does, it must match."""
    if "agent" in prop and prop["agent"] != agent_id:
        return False, R_IMPERSONATION, "proposal claims to be %r, submitted by %r" % (
            prop.get("agent"), agent_id)
    return True, R_OK, "identity ok"


def check_state(prop, world, agent_id):
    """Resource / permission validation against the world. Returns (ok, rule, reason)."""
    op = prop["op"]
    if op == "claim":
        amt = prop["amount"]
        if amt > world.pool:
            return False, R_OVER_POOL, "claim %d exceeds remaining pool %d" % (
                amt, world.pool)
        return True, R_OK, "claim ok"
    if op == "release":
        amt = prop["amount"]
        if amt > world.holding(agent_id):
            return False, R_OVER_HOLDING, "release %d exceeds holding %d" % (
                amt, world.holding(agent_id))
        return True, R_OK, "release ok"
    if op == "message":
        to = prop["to"]
        if to != "all" and to not in world.agents:
            return False, R_UNKNOWN_PEER, "unknown recipient %r" % (to,)
        return True, R_OK, "message ok"
    if op == "spawn":
        if world.spawn_budget <= 0:
            return False, R_NO_SPAWN_BUDGET, "spawn budget exhausted"
        if prop["role"] not in world.allowed_roles:
            return False, R_UNKNOWN_ROLE, "unknown role %r" % (prop["role"],)
        return True, R_OK, "spawn ok"
    return True, R_OK, "no state constraint"


def screen(prop, world, agent_id):
    """Full gate: shape -> identity -> state. Returns (ok, rule, reason)."""
    ok, rule, why = check_shape(prop)
    if not ok:
        return False, rule, why
    ok, rule, why = check_identity(prop, agent_id)
    if not ok:
        return False, rule, why
    return check_state(prop, world, agent_id)


# ------------------------------------------------------------------
# the escape corpus: adversarial proposals the gate must refuse
# ------------------------------------------------------------------
# This is the "how would you test that it holds?" half of Track 1. Every
# item here is run through the gate on every CI run, and every one must be
# refused with the expected rule id.

ESCAPE_CORPUS = [
    # (name, proposal, expected rule)
    ("unknown-op", {"op": "exec", "amount": 1}, R_UNKNOWN_OP),
    ("op-not-string", {"op": 7}, R_UNKNOWN_OP),
    ("no-op", {"amount": 1}, R_UNKNOWN_OP),
    ("negative-claim", {"op": "claim", "amount": -5}, R_BAD_AMOUNT),
    ("zero-claim", {"op": "claim", "amount": 0}, R_BAD_AMOUNT),
    ("huge-claim", {"op": "claim", "amount": 10 ** 9}, R_OVER_CAP),
    ("float-claim", {"op": "claim", "amount": 3.5}, R_BAD_TYPE),
    ("bool-claim", {"op": "claim", "amount": True}, R_BAD_TYPE),
    ("string-claim", {"op": "claim", "amount": "5"}, R_BAD_TYPE),
    ("none-claim", {"op": "claim", "amount": None}, R_BAD_TYPE),
    ("missing-amount", {"op": "claim"}, R_MISSING_FIELD),
    ("extra-field", {"op": "claim", "amount": 1, "sudo": True}, R_UNKNOWN_FIELD),
    ("smuggled-path", {"op": "claim", "amount": 1, "path": "../../etc/passwd"},
     R_UNKNOWN_FIELD),
    ("not-a-dict", ["claim", 1], R_BAD_TYPE),
    ("dot-key", {"op": "read", "key": "../secret"}, R_BAD_KEY),
    ("slash-key", {"op": "read", "key": "a/b"}, R_BAD_KEY),
    ("empty-key", {"op": "read", "key": ""}, R_BAD_KEY),
    ("uppercase-key", {"op": "read", "key": "Shared"}, R_BAD_KEY),
    ("private-ns", {"op": "read", "key": "private_u_003"}, R_RESERVED_KEY),
    ("system-ns", {"op": "write", "key": "system_flag", "value": "1"},
     R_RESERVED_KEY),
    ("nul-in-value", {"op": "write", "key": "note", "value": "a\x00b"},
     R_CONTROL_CHAR),
    ("newline-in-key", {"op": "write", "key": "no\nte", "value": "x"},
     R_CONTROL_CHAR),
    ("del-char", {"op": "write", "key": "note", "value": "a\x7fb"},
     R_CONTROL_CHAR),
    # Fullwidth and ligature keys both fail the canonicalisation check
    # before they ever reach the namespace grammar.
    ("fullwidth-key", {"op": "read", "key": "ｓｈａｒｅｄ"}, R_NON_CANONICAL),
    ("noncanonical-key", {"op": "read", "key": "ﬁle"}, R_NON_CANONICAL),
    ("value-too-long", {"op": "write", "key": "note", "value": "x" * 5000},
     R_TOO_LONG),
    ("body-too-long", {"op": "message", "to": "all", "body": "y" * 5000},
     R_TOO_LONG),
    ("impersonate", {"op": "claim", "amount": 1, "agent": "someone_else"},
     R_IMPERSONATION),
    ("claim-own-name", {"op": "claim", "amount": 1, "agent": "SELF"}, R_OK),
    ("unknown-peer", {"op": "message", "to": "ghost", "body": "hi"},
     R_UNKNOWN_PEER),
    ("non-string-to", {"op": "message", "to": 12, "body": "hi"}, R_BAD_TYPE),
    ("bad-role", {"op": "spawn", "role": "root"}, R_UNKNOWN_ROLE),
]
