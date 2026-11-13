# ledger-layer — P4 Ledger

README.md — repository purpose and layer contract for P4 Ledger.

Function:
    This repository implements primitive layer P4 of the Forge Stack:
    ChronoSCRIBE, the hash-chained, append-only ledger. It consumes P1
    Envelope v2 for the underlying cryptographic primitives.

Layer:    P4 — Ledger
Depends:  P1 Envelope v2 (envelope_v2.py), checked out as the sibling
          directory `../envelope-layer`
Consumed: P5 Genesis, P6 Canon Verify, P7 Record
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
Status:   2.0.0 frozen. ledger_v2.py (SPEC_V2.md) is the strict layer
          over 1.0.0 (ledger.py, SPEC.md), also frozen.
New code imports `ledger_v2`, not `ledger`.

Tests: `python -m pytest` (needs `cryptography` and `pytest`).
