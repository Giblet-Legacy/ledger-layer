# SPEC V2 — ledger-layer (P4 Ledger, strict layer)

SPEC_V2.md — specification for ledger_v2.py, the layer above P4 v1.0.0.

Function:
    Specifies ledger_v2.py, a strict layer over the frozen P4 v1.0.0
    primitive (ledger.py). It closes the divergences D1–D8 recorded in
    NOTES.md without editing ledger.py (Immutable Rule).

    SPEC.md v1.0.0 remains authoritative for everything this document
    does not change. Where this document is silent, SPEC.md v1.0.0
    applies unchanged.

Layer:     P4 — Ledger, v2 (strict)
Depends:   ledger.py (P4 v1.0.0), envelope_v2.py (P1 v2.0.0)
Consumed:  P5 Genesis, P6 Canon Verify, P7 Record — new code imports
           ledger_v2, not ledger
Version:   SPEC V2 2.0.0 (draft — pre-freeze)
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

---

## 1. Compatibility guarantee

- **Entries.** For the same ledger state, record and key, ledger_v2
  appends the same entry as ledger.py v1.0.0: the same seq, prev,
  record, signer, hash and signature (Ed25519 is deterministic). v2
  obtains the entry by calling v1's append_entry, so this holds by
  construction.
- **Ledgers.** Every ledger v2 accepts, v1 also accepts. A v1 ledger
  written with LF line endings (any v1 ledger written on the S24) is
  accepted by v2.

v2 differs from v1 only by **rejecting** inputs that v1 accepted or
crashed on. That narrowing is why the major version is 2.

## 2. On-disk form (resolves D1, D2)

A ledger file is the concatenation, for each entry in order, of

    json.dumps(entry, separators=(",", ":")).encode("ascii") + b"\n"

which is exactly what append_entry writes. Hence:

- Line endings are LF only. Any `\r` byte makes the ledger invalid.
- No blank lines. The file ends with `\n`.
- Each line is a JSON object with exactly the six keys, in the order
  `seq, prev, record, signer, hash, signature`, and no others.
- Byte-for-byte compact form: re-serialising a parsed line must give
  back the same bytes. This rejects whitespace, duplicate keys and
  alternative escapes.

Field types:

| Field       | Type                                         |
|-------------|----------------------------------------------|
| `seq`       | int, not bool, ≥ 0                           |
| `prev`      | str, 64 lowercase hex characters             |
| `record`    | JSON object (dict)                           |
| `signer`    | str                                          |
| `hash`      | str, 64 lowercase hex characters             |
| `signature` | str, 128 lowercase hex characters            |

All other rules (genesis, chaining, hash, signature over the raw
32-byte digest, single signer) are SPEC.md v1.0.0 §1–§3, unchanged.

## 3. Function contracts

### 3.1 verify_ledger(ledger_path, public_key) -> bool (resolves D3, D4)

- Raises TypeError if public_key is not an Ed25519PublicKey.
- Returns False if the file does not exist **or is empty**. A ledger
  has at least its genesis entry.
- Returns False, and never raises, for any file content that breaks
  §2 or SPEC.md v1.0.0.
- Otherwise returns True.

### 3.2 append_entry(ledger_path, record, private_key) -> dict (resolves D5–D7)

- Raises TypeError if private_key is not an Ed25519PrivateKey.
- Raises TypeError if record is not a dict.
- Raises ValueError if record contains NaN or ±Infinity (P1 v2).
- Raises TypeError if record is not plain JSON, i.e. if the written
  line would not read back equal to the returned entry (non-str keys,
  tuples). Otherwise the caller would hold an entry that differs from
  the ledger.
- If the file exists and is non-empty, it must pass
  `verify_ledger(ledger_path, private_key.public_key())`. Otherwise
  append_entry raises ValueError. This also refuses an append by a
  key other than the ledger's signer.
- On any error the file is unchanged.
- Otherwise it writes one line in the §2 form (binary mode, LF), then
  flushes and fsyncs, and returns the entry.
- Missing or empty file: the genesis entry, as SPEC.md v1.0.0 §3.

Concurrent writers are out of scope: one process appends to a ledger
at a time.

## 4. Import path (resolves D8)

ledger_v2 finds P1 at the `envelope-layer` directory that is a sibling
of this repository's directory, resolved from the location of
ledger_v2.py, not from the current working directory.

## 5. Tests

test_ledger_v2.py is the executable form of §1–§4. It is written
before ledger_v2.py and run red first.
