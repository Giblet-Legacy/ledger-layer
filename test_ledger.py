"""
test_ledger.py — P4 Ledger test suite

Function:
    Executable expression of SPEC.md. Written before ledger.py
    per build discipline.

Functions in this file:
    1. key
    2. temp_ledger
    3. test_append_genesis
    4. test_append_multiple
    5. test_verify_ledger_valid
    6. test_verify_ledger_tampered_record
    7. test_verify_ledger_broken_chain

Layer:    P4 — Ledger
Spec:     SPEC.md v1.0.0
Licence:  MSL-1.0
"""

import os
import sys
import json
import tempfile
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# Add P1 to path
sys.path.insert(0, os.path.abspath('../envelope-layer'))

import ledger

# ---------------------------------------------------------------------------
# 1. key
# ---------------------------------------------------------------------------
@pytest.fixture
def key():
    return Ed25519PrivateKey.generate()

# ---------------------------------------------------------------------------
# 2. temp_ledger
# ---------------------------------------------------------------------------
@pytest.fixture
def temp_ledger():
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)

# ---------------------------------------------------------------------------
# 3. test_append_genesis
# ---------------------------------------------------------------------------
def test_append_genesis(temp_ledger, key):
    record = {"data": "first"}
    entry = ledger.append_entry(temp_ledger, record, key)
    
    assert entry["seq"] == 0
    assert entry["prev"] == "0" * 64
    assert entry["record"] == record
    assert "hash" in entry
    assert "signature" in entry

# ---------------------------------------------------------------------------
# 4. test_append_multiple
# ---------------------------------------------------------------------------
def test_append_multiple(temp_ledger, key):
    e1 = ledger.append_entry(temp_ledger, {"data": "one"}, key)
    e2 = ledger.append_entry(temp_ledger, {"data": "two"}, key)
    e3 = ledger.append_entry(temp_ledger, {"data": "three"}, key)
    
    assert e2["seq"] == 1
    assert e2["prev"] == e1["hash"]
    
    assert e3["seq"] == 2
    assert e3["prev"] == e2["hash"]

# ---------------------------------------------------------------------------
# 5. test_verify_ledger_valid
# ---------------------------------------------------------------------------
def test_verify_ledger_valid(temp_ledger, key):
    ledger.append_entry(temp_ledger, {"data": "one"}, key)
    ledger.append_entry(temp_ledger, {"data": "two"}, key)
    ledger.append_entry(temp_ledger, {"data": "three"}, key)
    
    assert ledger.verify_ledger(temp_ledger, key.public_key()) is True

# ---------------------------------------------------------------------------
# 6. test_verify_ledger_tampered_record
# ---------------------------------------------------------------------------
def test_verify_ledger_tampered_record(temp_ledger, key):
    ledger.append_entry(temp_ledger, {"data": "one"}, key)
    ledger.append_entry(temp_ledger, {"data": "two"}, key)
    
    # Tamper with the file
    with open(temp_ledger, "r") as f:
        lines = f.readlines()
    
    entry = json.loads(lines[0])
    entry["record"]["data"] = "tampered"
    
    with open(temp_ledger, "w") as f:
        f.write(json.dumps(entry, separators=(',', ':')) + "\n")
        f.write(lines[1])
        
    assert ledger.verify_ledger(temp_ledger, key.public_key()) is False

# ---------------------------------------------------------------------------
# 7. test_verify_ledger_broken_chain
# ---------------------------------------------------------------------------
def test_verify_ledger_broken_chain(temp_ledger, key):
    ledger.append_entry(temp_ledger, {"data": "one"}, key)
    ledger.append_entry(temp_ledger, {"data": "two"}, key)
    
    with open(temp_ledger, "r") as f:
        lines = f.readlines()
        
    entry = json.loads(lines[1])
    entry["prev"] = "badhash" * 8
    
    with open(temp_ledger, "w") as f:
        f.write(lines[0])
        f.write(json.dumps(entry, separators=(',', ':')) + "\n")
        
    assert ledger.verify_ledger(temp_ledger, key.public_key()) is False
