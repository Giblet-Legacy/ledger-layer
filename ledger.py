"""
ledger.py — P4 Ledger primitive layer

Function:
    Implements ChronoSCRIBE: the hash-chained, append-only .jsonl
    ledger. Consumes envelope_v2 (P1) for canonicalisation and
    signing.

Public API:
    1. append_entry    — Hash, sign, and append a record to the ledger.
    2. verify_ledger   — Read and verify the entire chain.

Layer:    P4 — Ledger
Depends:  P1 Envelope v2 (envelope_v2.py)
Consumed: P5 Genesis, P6 Canon Verify, P7 Record
Version:  1.0.0 (on freeze; 0.0.0-dev until then)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys
import json

# Import P1
sys.path.insert(0, os.path.abspath('../envelope-layer'))
import envelope_v2 as envelope

GENESIS_PREV = "0" * 64

# ---------------------------------------------------------------------------
# 1. append_entry
#    Builds the unsigned entry, hashes it, signs the digest, and appends.
# ---------------------------------------------------------------------------
def append_entry(ledger_path, record, private_key):
    seq = 0
    prev = GENESIS_PREV
    
    # Read existing file to get the last hash
    if os.path.exists(ledger_path) and os.path.getsize(ledger_path) > 0:
        with open(ledger_path, "r") as f:
            lines = f.readlines()
            if lines:
                last_entry = json.loads(lines[-1])
                seq = last_entry["seq"] + 1
                prev = last_entry["hash"]
                
    # Build unsigned entry
    did_key = envelope.did_key_encode(private_key.public_key())
    unsigned = {
        "seq": seq,
        "prev": prev,
        "record": record,
        "signer": did_key
    }
    
    # Canonicalise and hash
    canonical_bytes = envelope.canonical_bytes(unsigned)
    entry_hash = envelope.sha256_hex(canonical_bytes)
    entry_digest = envelope.sha256_digest(canonical_bytes)
    
    # Sign the raw digest
    sig_bytes = envelope.sign_bytes(entry_digest, private_key)
    
    # Build final entry
    entry = dict(unsigned)
    entry["hash"] = entry_hash
    entry["signature"] = sig_bytes.hex()
    
    # Write to file
    with open(ledger_path, "a") as f:
        f.write(json.dumps(entry, separators=(',', ':')) + "\n")
        
    return entry

# ---------------------------------------------------------------------------
# 2. verify_ledger
#    Reads the file line by line, reconstructs the chain, and verifies.
# ---------------------------------------------------------------------------
def verify_ledger(ledger_path, public_key):
    if not os.path.exists(ledger_path):
        return False
        
    expected_did = envelope.did_key_encode(public_key)
    expected_seq = 0
    expected_prev = GENESIS_PREV
    
    with open(ledger_path, "r") as f:
        for line in f:
            if not line.strip():
                continue
                
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                return False
                
            # Verify structural chain
            if entry.get("seq") != expected_seq:
                return False
            if entry.get("prev") != expected_prev:
                return False
            if entry.get("signer") != expected_did:
                return False
                
            # Extract signature and hash
            try:
                sig_bytes = bytes.fromhex(entry["signature"])
                claimed_hash = entry["hash"]
            except (KeyError, ValueError):
                return False
                
            # Rebuild unsigned entry
            unsigned = {
                "seq": entry["seq"],
                "prev": entry["prev"],
                "record": entry["record"],
                "signer": entry["signer"]
            }
            
            # Recalculate hash and digest
            canonical_bytes = envelope.canonical_bytes(unsigned)
            actual_hash = envelope.sha256_hex(canonical_bytes)
            actual_digest = envelope.sha256_digest(canonical_bytes)
            
            if actual_hash != claimed_hash:
                return False
                
            # Verify signature
            if not envelope.verify_bytes(actual_digest, sig_bytes, public_key):
                return False
                
            # Advance chain state
            expected_seq += 1
            expected_prev = claimed_hash
            
    return True
