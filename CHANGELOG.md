# CHANGELOG — ledger-layer (P4 Ledger)

CHANGELOG.md — build history for P4 Ledger, latest entry at top.

## [v1.0.0] — 2026-11-11

### Good
- `ledger.py` implemented to SPEC v1.0.0.
- 5/5 pytest tests pass.
- Implements ChronoSCRIBE: hash-chained, append-only .jsonl ledger.
- Signs the raw 32-byte digest, not the canonical bytes (Ledger Rule).

### Bad
- (none)

### Ugly
- (none)

### Good
- Repository scaffolded: `Giblet-Legacy/ledger-layer` created for P4.
- Depends on P1 Envelope v2.0.0.

### Bad
- (none)

### Ugly
- (none)
