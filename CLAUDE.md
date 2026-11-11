# Forge Stack Context — P4 Ledger

CLAUDE.md — Context briefing for AI assistants working in this repository.

Function:
    Instructs the AI assistant on the strict architectural rules of the
    Forge Stack. Do not hallucinate external frameworks. Reason strictly
    within these boundaries.

## The Immutable Rule
Never rewrite a primitive. Add a layer.
If `ledger.py` needs a change, we do NOT edit it. We create a v2 layer above it.

## Dual-Device Workflow
We build on an S24 (Termux) and a laptop (VS Code). State is confirmed, never assumed. Always use LF line endings. Commit messages must be clear. We use the Good/Bad/Ugly CHANGELOG format (latest at top).

## Header Discipline
Every file MUST have a top header paragraph explaining its function.
Every function MUST have a numbered header (e.g., `# 1. append_entry`).

## P4 Architecture Specifics
- Depends on `envelope_v2` (P1 v2.0.0).
- Ledger rule: the Ed25519 signature covers the raw 32-byte SHA-256 digest of the unsigned entry.
- Hash-chained, append-only `.jsonl` format.
