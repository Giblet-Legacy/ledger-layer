"""
test_ledger_v2.py — P4 Ledger v2 (strict layer) test suite

Function:
    Executable expression of SPEC_V2.md. Written before ledger_v2.py
    and run red first. Proves two things: (1) v2 appends the same
    entries as the frozen v1 primitive, and the two accept each
    other's LF ledgers; (2) v2 rejects, or returns False, where v1
    crashed or accepted out-of-contract input (NOTES.md D1–D8).

Functions in this file (pytest-collected):
    1.  test_public_api                  — two names, both callable
    2.  test_entry_identity_with_v1      — same entries as v1, byte for byte
    3.  test_ledgers_cross_verify        — v1 LF ledger ⇄ v2 ledger
    4.  test_lf_only_on_disk             — D1: no CR bytes written
    5.  test_empty_and_missing_false     — D4
    6.  test_malformed_returns_false     — D2, D3: False, never raises
    7.  test_tamper_still_false          — v1 rejections kept
    8.  test_append_refuses_invalid      — D6: ValueError, file unchanged
    9.  test_append_refuses_foreign_key  — D5
    10. test_append_type_errors          — D7, key types
    11. test_append_non_finite_rejected  — P1 v2 rule, file unchanged
    12. test_verify_type_error           — public_key type
    13. test_import_from_any_cwd         — D8

Internal helpers:
    14. _compact — the SPEC_V2 §2 line form of an entry
    15. _write     — replace a ledger file's bytes
    16. _mutations — out-of-contract variants of one entry

Fixtures:
    17. key  — fresh Ed25519 private key
    18. path — ledger path in a fresh temp directory (file absent)

Layer:    P4 — Ledger, v2 (strict)
Spec:     SPEC_V2.md 2.0.0 (over SPEC.md v1.0.0)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import json
import os
import subprocess
import sys

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import ledger
import ledger_v2

HERE = os.path.dirname(os.path.abspath(__file__))
RECORDS = [{"data": "one"}, {"data": "two", "n": [1, 2.5, None]}, {"é": "ü"}]


# ---------------------------------------------------------------------------
# 17. key
# ---------------------------------------------------------------------------
@pytest.fixture
def key():
    return Ed25519PrivateKey.generate()


# ---------------------------------------------------------------------------
# 18. path
#     A ledger path in a fresh directory; the file does not exist yet.
# ---------------------------------------------------------------------------
@pytest.fixture
def path(tmp_path):
    return str(tmp_path / "ledger.jsonl")


# ---------------------------------------------------------------------------
# 14. _compact
# ---------------------------------------------------------------------------
def _compact(entry):
    return json.dumps(entry, separators=(",", ":")).encode("ascii") + b"\n"


# ---------------------------------------------------------------------------
# 15. _write
# ---------------------------------------------------------------------------
def _write(path, data):
    with open(path, "wb") as f:
        f.write(data)


# ---------------------------------------------------------------------------
# 1. test_public_api
# ---------------------------------------------------------------------------
def test_public_api():
    assert callable(ledger_v2.append_entry)
    assert callable(ledger_v2.verify_ledger)


# ---------------------------------------------------------------------------
# 2. test_entry_identity_with_v1
# ---------------------------------------------------------------------------
def test_entry_identity_with_v1(tmp_path, key):
    p1, p2 = str(tmp_path / "v1.jsonl"), str(tmp_path / "v2.jsonl")
    for record in RECORDS:
        assert ledger.append_entry(p1, record, key) == ledger_v2.append_entry(p2, record, key)


# ---------------------------------------------------------------------------
# 3. test_ledgers_cross_verify
# ---------------------------------------------------------------------------
def test_ledgers_cross_verify(tmp_path, key):
    p1, p2 = str(tmp_path / "v1.jsonl"), str(tmp_path / "v2.jsonl")
    for record in RECORDS:
        ledger.append_entry(p1, record, key)
        ledger_v2.append_entry(p2, record, key)
    # v1 writes CRLF on Windows (D1); an LF v1 ledger is in contract.
    with open(p1, "rb") as f:
        data = f.read().replace(b"\r\n", b"\n")
    _write(p1, data)
    with open(p2, "rb") as f:
        assert f.read() == data
    assert ledger_v2.verify_ledger(p1, key.public_key()) is True
    assert ledger.verify_ledger(p2, key.public_key()) is True


# ---------------------------------------------------------------------------
# 4. test_lf_only_on_disk
# ---------------------------------------------------------------------------
def test_lf_only_on_disk(path, key):
    for record in RECORDS:
        ledger_v2.append_entry(path, record, key)
    with open(path, "rb") as f:
        data = f.read()
    assert b"\r" not in data
    assert data.endswith(b"\n") and data.count(b"\n") == len(RECORDS)
    assert ledger_v2.verify_ledger(path, key.public_key()) is True


# ---------------------------------------------------------------------------
# 5. test_empty_and_missing_false
# ---------------------------------------------------------------------------
def test_empty_and_missing_false(path, key):
    assert ledger_v2.verify_ledger(path, key.public_key()) is False
    _write(path, b"")
    assert ledger_v2.verify_ledger(path, key.public_key()) is False
    entry = ledger_v2.append_entry(path, {"a": 1}, key)
    assert entry["seq"] == 0 and entry["prev"] == "0" * 64


# ---------------------------------------------------------------------------
# 16. _mutations
#     Yield (name, file bytes) for out-of-contract variants of one entry.
# ---------------------------------------------------------------------------
def _mutations(entry):
    good = _compact(entry)
    yield "crlf", good[:-1] + b"\r\n"
    yield "no final newline", good[:-1]
    yield "blank line", good + b"\n"
    yield "not json", b"not json\n"
    yield "json array", b"[1,2]\n"
    yield "non-compact", json.dumps(entry).encode() + b"\n"
    yield "duplicate key", good[:-2] + b',"seq":0}\n'
    reordered = {k: entry[k] for k in reversed(list(entry))}
    yield "key order", _compact(reordered)
    for field in entry:
        d = dict(entry)
        del d[field]
        yield "missing " + field, _compact(d)
    for field, bad in [("seq", False), ("seq", "0"), ("seq", -1),
                       ("prev", 0), ("prev", "0" * 63),
                       ("record", [1]), ("record", None),
                       ("signer", 7),
                       ("hash", entry["hash"].upper()), ("hash", 5),
                       ("signature", 5), ("signature", entry["signature"].upper()),
                       ("signature", "zz" * 64)]:
        d = dict(entry)
        d[field] = bad
        yield "%s=%r" % (field, bad), _compact(d)
    d = dict(entry)
    d["extra"] = "smuggled"
    yield "extra field", _compact(d)


# ---------------------------------------------------------------------------
# 6. test_malformed_returns_false
# ---------------------------------------------------------------------------
def test_malformed_returns_false(path, key):
    entry = ledger_v2.append_entry(path, {"data": "one"}, key)
    for name, data in _mutations(entry):
        _write(path, data)
        assert ledger_v2.verify_ledger(path, key.public_key()) is False, name


# ---------------------------------------------------------------------------
# 7. test_tamper_still_false
# ---------------------------------------------------------------------------
def test_tamper_still_false(path, key):
    e0 = ledger_v2.append_entry(path, {"data": "one"}, key)
    e1 = ledger_v2.append_entry(path, {"data": "two"}, key)
    tampered = dict(e0, record={"data": "tampered"})
    _write(path, _compact(tampered) + _compact(e1))
    assert ledger_v2.verify_ledger(path, key.public_key()) is False
    _write(path, _compact(e0) + _compact(dict(e1, prev="ab" * 32)))
    assert ledger_v2.verify_ledger(path, key.public_key()) is False
    _write(path, _compact(e1))
    assert ledger_v2.verify_ledger(path, key.public_key()) is False
    other = Ed25519PrivateKey.generate().public_key()
    _write(path, _compact(e0) + _compact(e1))
    assert ledger_v2.verify_ledger(path, other) is False


# ---------------------------------------------------------------------------
# 8. test_append_refuses_invalid
# ---------------------------------------------------------------------------
def test_append_refuses_invalid(path, key):
    entry = ledger_v2.append_entry(path, {"data": "one"}, key)
    for name, data in _mutations(entry):
        _write(path, data)
        with pytest.raises(ValueError):
            ledger_v2.append_entry(path, {"data": "two"}, key)
        with open(path, "rb") as f:
            assert f.read() == data, name


# ---------------------------------------------------------------------------
# 9. test_append_refuses_foreign_key
# ---------------------------------------------------------------------------
def test_append_refuses_foreign_key(path, key):
    ledger_v2.append_entry(path, {"data": "one"}, key)
    with open(path, "rb") as f:
        before = f.read()
    with pytest.raises(ValueError):
        ledger_v2.append_entry(path, {"data": "two"}, Ed25519PrivateKey.generate())
    with open(path, "rb") as f:
        assert f.read() == before


# ---------------------------------------------------------------------------
# 10. test_append_type_errors
# ---------------------------------------------------------------------------
def test_append_type_errors(path, key):
    for record in ([1, 2], "x", None, 5, {1: "int key"}, {"a": (1, 2)}):
        with pytest.raises(TypeError):
            ledger_v2.append_entry(path, record, key)
    for bad_key in (None, b"\x00" * 32, key.public_key()):
        with pytest.raises(TypeError):
            ledger_v2.append_entry(path, {"a": 1}, bad_key)
    assert not os.path.exists(path)


# ---------------------------------------------------------------------------
# 11. test_append_non_finite_rejected
# ---------------------------------------------------------------------------
def test_append_non_finite_rejected(path, key):
    ledger_v2.append_entry(path, {"a": 1}, key)
    with open(path, "rb") as f:
        before = f.read()
    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError):
            ledger_v2.append_entry(path, {"x": [bad]}, key)
    with open(path, "rb") as f:
        assert f.read() == before


# ---------------------------------------------------------------------------
# 12. test_verify_type_error
# ---------------------------------------------------------------------------
def test_verify_type_error(path, key):
    ledger_v2.append_entry(path, {"a": 1}, key)
    for bad_key in (None, key, key.public_key().public_bytes_raw()):
        with pytest.raises(TypeError):
            ledger_v2.verify_ledger(path, bad_key)


# ---------------------------------------------------------------------------
# 13. test_import_from_any_cwd
# ---------------------------------------------------------------------------
def test_import_from_any_cwd(tmp_path):
    code = ("import sys; sys.path.insert(0, %r); import ledger_v2; "
            "print(ledger_v2.verify_ledger.__name__)" % HERE)
    out = subprocess.run([sys.executable, "-c", code], cwd=str(tmp_path),
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "verify_ledger"
