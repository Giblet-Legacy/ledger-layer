"""
ledger_v2.py — P4 Ledger v2, strict layer over the frozen v1 primitive

Function:
    The layer new code imports instead of ledger.py. It enforces the
    on-disk form of SPEC_V2.md §2 (LF only, compact lines, exactly six
    typed fields), makes verify_ledger return False instead of raising
    on bad content, and refuses to append onto an invalid ledger or
    under a foreign key (SPEC_V2.md §3). It never reimplements the
    primitive: every entry it writes is the dict returned by
    ledger.append_entry, and every chain/hash/signature check is
    ledger.verify_ledger (SPEC_V2.md §1).

    ledger.py is not edited (Immutable Rule). This file is the
    "add a layer" half of that rule.

Public API (same names and numbering as P4 v1.0.0):
    1. append_entry    — type checks, verify chain, v1 entry, LF write
    2. verify_ledger   — strict form check, then v1 chain verification

Internal helpers (not exported):
    3. _reject_constant — json.loads hook that fires on NaN/±Infinity
    4. _is_hex          — lowercase hex string of exact length
    5. _check_entry     — six keys, in order, with SPEC_V2 §2 types
    6. _parse_ledger    — bytes → entries, or None if not SPEC_V2 §2
    7. _compact         — the SPEC_V2 §2 line bytes for an entry
    8. _v1_verify       — v1 verify_ledger over exact bytes
    9. _v1_entry        — v1 append_entry after a given tail line
    10. _verify_data    — form check (6) then v1 verify (8) over bytes

Layer:    P4 — Ledger, v2 (strict)
Depends:  ledger.py (P4 v1.0.0), envelope_v2.py (P1 v2.0.0)
Consumed: P5 Genesis, P6 Canon Verify, P7 Record
Spec:     SPEC_V2.md 2.0.0 (over SPEC.md v1.0.0)
Version:  2.0.0 (frozen 2026-11-13)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import sys
import tempfile

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

# Resolve P1 and P4 v1 from this file's location, not the CWD (SPEC_V2 §4).
_HERE = os.path.dirname(os.path.abspath(__file__))
for _path in (os.path.join(os.path.dirname(_HERE), "envelope-layer"), _HERE):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import ledger as _v1  # noqa: E402

KEYS = ["seq", "prev", "record", "signer", "hash", "signature"]
_HEX = frozenset("0123456789abcdef")


# ---------------------------------------------------------------------------
# 3. _reject_constant
#    json.loads calls parse_constant only for the bare tokens NaN,
#    Infinity and -Infinity. They are not JSON; the line is rejected.
# ---------------------------------------------------------------------------
def _reject_constant(token):
    raise ValueError(f"non-finite float in ledger: {token}")


# ---------------------------------------------------------------------------
# 4. _is_hex
#    True if value is a str of exactly `length` lowercase hex characters.
# ---------------------------------------------------------------------------
def _is_hex(value, length):
    return isinstance(value, str) and len(value) == length and set(value) <= _HEX


# ---------------------------------------------------------------------------
# 5. _check_entry
#    SPEC_V2 §2 field table: exactly six keys, in order, typed.
# ---------------------------------------------------------------------------
def _check_entry(entry):
    if not isinstance(entry, dict) or list(entry) != KEYS:
        return False
    seq = entry["seq"]
    return (
        isinstance(seq, int) and not isinstance(seq, bool) and seq >= 0
        and _is_hex(entry["prev"], 64)
        and isinstance(entry["record"], dict)
        and isinstance(entry["signer"], str)
        and _is_hex(entry["hash"], 64)
        and _is_hex(entry["signature"], 128)
    )


# ---------------------------------------------------------------------------
# 6. _parse_ledger
#    Returns the list of entries if data is in SPEC_V2 §2 form (LF only,
#    final newline, no blank lines, every line byte-identical to its
#    compact re-serialisation, every entry well-typed). Else None.
#    Chain, hash and signature are not checked here — that is v1's job.
# ---------------------------------------------------------------------------
def _parse_ledger(data):
    if not data or b"\r" in data or not data.endswith(b"\n"):
        return None
    entries = []
    for line in data[:-1].split(b"\n"):
        try:
            entry = json.loads(line.decode("ascii"), parse_constant=_reject_constant)
        except ValueError:  # includes JSONDecodeError and UnicodeDecodeError
            return None
        if not _check_entry(entry) or _compact(entry) != line + b"\n":
            return None
        entries.append(entry)
    return entries


# ---------------------------------------------------------------------------
# 7. _compact
#    One ledger line: compact JSON, ASCII, LF-terminated. Identical to
#    the text v1 writes, minus the platform newline translation (D1).
# ---------------------------------------------------------------------------
def _compact(entry):
    return json.dumps(entry, separators=(",", ":")).encode("ascii") + b"\n"


# ---------------------------------------------------------------------------
# 8. _v1_verify
#    Runs v1 verify_ledger over exactly `data` (a private copy), so the
#    bytes v1 checks are the bytes v2 already form-checked.
# ---------------------------------------------------------------------------
def _v1_verify(data, public_key):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "ledger.jsonl")
        with open(path, "wb") as f:
            f.write(data)
        try:
            return _v1.verify_ledger(path, public_key) is True
        except (ValueError, TypeError, KeyError):
            return False


# ---------------------------------------------------------------------------
# 9. _v1_entry
#    Runs v1 append_entry against a private file holding only `tail`
#    (the last ledger line, or b"" for genesis) and returns v1's entry.
#    v1 reads only the last line, so the entry is the one v1 would
#    append to the real ledger. The real ledger is not touched.
# ---------------------------------------------------------------------------
def _v1_entry(tail, record, private_key):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "ledger.jsonl")
        with open(path, "wb") as f:
            f.write(tail)
        return _v1.append_entry(path, record, private_key)


# ---------------------------------------------------------------------------
# 1. append_entry
#    SPEC_V2 §3.2. Checks types, verifies the existing chain under this
#    key, takes the entry from v1, writes it as one LF line, fsyncs.
#    On any error the ledger file is unchanged.
# ---------------------------------------------------------------------------
def append_entry(ledger_path, record, private_key):
    if not isinstance(private_key, Ed25519PrivateKey):
        raise TypeError(f"private_key must be Ed25519PrivateKey, got {type(private_key).__name__}")
    if not isinstance(record, dict):
        raise TypeError(f"record must be dict, got {type(record).__name__}")

    tail = b""
    if os.path.exists(ledger_path) and os.path.getsize(ledger_path) > 0:
        with open(ledger_path, "rb") as f:
            data = f.read()
        if not _verify_data(data, private_key.public_key()):
            raise ValueError("refusing to append: ledger does not verify under this key")
        tail = data[data.rstrip(b"\n").rfind(b"\n") + 1:]

    entry = _v1_entry(tail, record, private_key)
    line = _compact(entry)
    if json.loads(line) != entry:
        raise TypeError("record must be plain JSON: str keys, lists not tuples")

    with open(ledger_path, "ab") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())
    return entry


# ---------------------------------------------------------------------------
# 2. verify_ledger
#    SPEC_V2 §3.1. TypeError on a wrong key type; otherwise True only if
#    the file exists, is non-empty, is in SPEC_V2 §2 form and passes v1.
#    Never raises for file content.
# ---------------------------------------------------------------------------
def verify_ledger(ledger_path, public_key):
    if not isinstance(public_key, Ed25519PublicKey):
        raise TypeError(f"public_key must be Ed25519PublicKey, got {type(public_key).__name__}")
    try:
        with open(ledger_path, "rb") as f:
            data = f.read()
    except OSError:
        return False
    return _verify_data(data, public_key)


# ---------------------------------------------------------------------------
# 10. _verify_data
#     Shared by 1 and 2: SPEC_V2 §2 form check, then v1 over the same bytes.
# ---------------------------------------------------------------------------
def _verify_data(data, public_key):
    return _parse_ledger(data) is not None and _v1_verify(data, public_key)
