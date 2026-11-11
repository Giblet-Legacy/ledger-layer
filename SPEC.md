# SPEC — ledger-layer (P4 Ledger)

SPEC.md — the complete layer specification for P4 Ledger.

Function:
    This document is the authoritative specification for primitive
    layer P4 of the Forge Stack. It defines the hash-chained,
    append-only .jsonl ledger format.

Layer:     P4 — Ledger
Depends:   P1 Envelope v2 (envelope_v2.py)
Consumed:  P5 Genesis, P6 Canon Verify, P7 Record
Version:   SPEC 1.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

## 1. The Ledger Entry Format

A ledger is a `.jsonl` file (JSON Lines). Each line is a complete JSON object representing one entry. Whitespace is prohibited (compact JSON).

The entry structure:
{
  "seq": 0,
  "prev": "0000000000000000000000000000000000000000000000000000000000000000",
  "record": { ... signed capsule ... },
  "signer": "did:key:z6Mk...",
  "hash": "hex-encoded-sha256",
  "signature": "hex-encoded-ed25519-sig"
}

## 2. The Ledger Cryptography Rule

To append an entry:
1. Construct the "unsigned entry": a dict with exactly seq, prev, record, and signer.
2. Canonicalise the unsigned entry via `envelope_v2.canonical_bytes()`.
3. Calculate the `hash` (SHA-256 hex) of the canonical bytes.
4. Calculate the raw 32-byte SHA-256 digest.
5. Sign the raw 32-byte digest via `envelope_v2.sign_bytes()`.
6. Append `hash` and `signature` to the entry.
7. Write the entry as a single line of compact JSON to the file.

## 3. The Genesis Rule

If the file is empty or does not exist, the first entry must be:
- `seq`: 0
- `prev`: "0000000000000000000000000000000000000000000000000000000000000000"

Every subsequent entry must have `seq` incremented by 1, and `prev` set to the `hash` of the previous entry.

## 4. Function Contracts

### 4.1 append_entry(ledger_path: str, record: dict, private_key) -> dict
- Input: Path to `.jsonl`, a record dictionary, an Ed25519 private key.
- Output: The newly created ledger entry dictionary.
- Purity: Impure (file I/O).

### 4.2 verify_ledger(ledger_path: str, public_key) -> bool
- Input: Path to `.jsonl`, an Ed25519 public key.
- Output: True if the entire chain is valid, False otherwise.
- Purity: Impure (file I/O).
