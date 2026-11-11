# NOTES — ledger-layer (P4 Ledger)

NOTES.md — open questions, divergences and decisions for P4 Ledger.

## Open questions
- (none)

## Divergences from v1.2.1 specification
- (none)

## Decisions
- The `hash` field is the hex digest of the canonical unsigned entry.
- The `signature` is the hex signature of the *raw digest bytes*, not 
  the canonical string. This aligns with the P1 distinction.
