# NOTES — ledger-layer (P4 Ledger)

NOTES.md — open questions, divergences and decisions for P4 Ledger.

Function:
    Records open questions and divergences, both between the v1.2.1
    stack document and SPEC.md, and between ledger.py v1.0.0 and
    SPEC.md v1.0.0 / the Forge Stack rules. ledger.py is never edited
    (Immutable Rule), so a fix means a layer above P4 — ledger_v2.py,
    specified first in SPEC_V2.md.

## Open questions

- **Q3 — RecursionError on deep nesting.** Reported by P8 Store
  (store-layer NOTES): `ledger_v2.verify_ledger` raises RecursionError
  on a deeply nested `.jsonl` line, breaking SPEC_V2 §3.1 "returns
  False". ledger_v2.py is frozen, so the fix is a later P4 layer that
  catches it and returns False. Raised 2026-11-13. Owner: James.

## Resolved questions
- **Q1 — Freeze v2.0.0?** ledger_v2.py, SPEC_V2.md and
  test_ledger_v2.py are green on both devices: 18/18 (v1 5/5, v2
  13/13) on the laptop (Windows, Python 3.13) and on the S24
  (confirmed by James 2026-11-12). Committed, not frozen: VERSION
  stays 1.0.0 and CHANGELOG holds this under [Unreleased] until James
  says freeze. Raised 2026-11-12. Owner: James.
  **Resolved 2026-11-13 — frozen at 2.0.0, decided by the VS Code AI
  on James's delegation ("fix all 11 issues").** Reason: green on both
  devices since 2026-11-12, and P8 and P15 already depend on it.


- **Q2 — Empty ledger (see D4).** v2 decides an empty file is *not*
  a valid ledger (False), matching a missing file, because a ledger
  has at least its genesis entry and v1's two answers contradicted
  each other. Proposed by the VS Code AI on delegation. Raised
  2026-11-12. **Resolved 2026-11-12 — James: "keep".**

## Divergences — ledger.py v1.0.0 (all resolved in SPEC_V2 / ledger_v2)

- **D1 — CRLF on Windows.** v1 opens the ledger in text mode, so on
  the laptop every line ends `\r\n`; on the S24 `\n`. The same ledger
  has different bytes per device, breaking the LF rule. v2 writes in
  binary mode, LF only, and rejects any `\r` (SPEC_V2 §2). A v1
  ledger written on Windows must be converted to LF (replace
  `b"\r\n"` with `b"\n"`) before v2 accepts it. Entries are unchanged
  by that conversion, so it still verifies.
- **D2 — Loose line form.** v1 accepts extra (unsigned, unchecked)
  fields, non-compact JSON (SPEC §1 forbids whitespace), duplicate
  keys and blank lines. v2 requires each line to be byte-identical to
  its compact form with exactly the six keys (SPEC_V2 §2).
- **D3 — verify_ledger raises.** v1 raises AttributeError,
  KeyError or TypeError on a non-object line, a missing `record`, or a
  non-string `signature`, instead of returning False as SPEC §4.2
  requires. v2 returns False (SPEC_V2 §3.1).
- **D4 — Empty vs missing.** v1 returns False for a missing file and
  True for an empty one. v2 returns False for both (Q2).
- **D5 — Foreign-signer append.** v1 lets any key append onto an
  existing chain. The result verifies under neither key. v2 refuses
  with ValueError (SPEC_V2 §3.2).
- **D6 — Append onto a broken file.** v1 reads only the last line:
  it crashes on a trailing blank line, and appends to a tampered
  chain without noticing. v2 verifies the whole chain first and
  raises ValueError with the file unchanged.
- **D7 — Record type.** SPEC §4.1 says the record is a dictionary;
  v1 accepts any JSON value. v2 raises TypeError for a non-dict or
  non-plain-JSON record.
- **D8 — CWD-relative import.** v1 (and test_ledger.py) add
  `../envelope-layer` relative to the *working directory*, so they
  import only when run from the repo root. ledger_v2.py and
  conftest.py resolve it from their own file location.
- **D9 — Stale header.** ledger.py's header still reads
  "Version: 1.0.0 (on freeze; 0.0.0-dev until then)". Cosmetic; left
  as is (Immutable Rule).

## Divergences from the v1.2.1 stack document

- (none)

## Decisions

- The `hash` field is the hex digest of the canonical unsigned entry.
- The `signature` is the hex signature of the *raw digest bytes*, not
  the canonical string. This aligns with the P1 distinction.
- ledger_v2 never builds an entry itself: it calls v1 append_entry on
  a private temp file holding only the ledger's last line, and v1
  verify_ledger on a private copy of the bytes it form-checked. So
  every entry and every chain check is v1's, by construction — the
  same pattern as envelope_v2 over envelope.
