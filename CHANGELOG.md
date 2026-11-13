# CHANGELOG — ledger-layer (P4 Ledger)

CHANGELOG.md — build history for P4 Ledger, latest entry at top.

Function:
    Records the Good / Bad / Ugly of every build step for this layer.
    Updated at every sign-off. Format never changes shape, even when a
    section is empty.

## [Unreleased]

### Good

- (none)

### Bad

- (none)

### Ugly

- (none)

## [v2.0.0] — 2026-11-13

### Good

- Frozen. NOTES Q1 resolved on James's delegation ("fix all 11
  issues", 2026-11-13): 18/18 green on the laptop and the S24 since
  2026-11-12, and P8 Store v2/v2.1 and P15 HAL v2 already build on it.
  Unblocks P5 genesis_v3 and the Cockpit's move to v2 layers.
- `SPEC_V2.md`: strict layer over P4 v1.0.0, written before any code.
- `test_ledger_v2.py`: 13 tests, written before ledger_v2.py and run
  red first. 18/18 pass (v1 5/5, v2 13/13) on the laptop — from the
  repo root and from any other directory — and on the S24.
- NOTES Q2 resolved (James: "keep"): an empty ledger verifies False.
- `ledger_v2.py`: resolves NOTES D1–D8. Every entry and every chain
  check is delegated to ledger.py, so v1 and v2 entries are
  byte-identical (tested both ways).
- `conftest.py`: both suites now run from any working directory.
- Numbered headers added to test_ledger.py (comments only); header
  paragraphs added to .gitattributes; `requirements.txt` added.
- README status corrected (it still said 0.0.0-dev after freeze).
- ledger.py untouched (Immutable Rule).

### Bad

- ledger.py v1.0.0 writes CRLF on Windows, crashes in verify_ledger
  on malformed lines, and lets a foreign key fork a chain (NOTES D1,
  D3, D5). Shipped in v1.0.0 because the five v1 tests never covered
  them.

- Frozen with one known fault, reported by P8 Store: verify_ledger
  raises RecursionError on a deeply nested line instead of returning
  False (NOTES Q3). The fix is a later P4 layer.

### Ugly

- Ledgers written by v1 on the laptop have CRLF endings and fail v2
  until converted to LF (NOTES D1).

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

## [v0.0.0-dev] — scaffold

### Good

- Repository scaffolded: `Giblet-Legacy/ledger-layer` created for P4.
- Depends on P1 Envelope v2.0.0.

### Bad

- (none)

### Ugly

- (none)
