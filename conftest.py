"""
conftest.py — pytest import-path setup for P4 Ledger

Function:
    Puts this repository and the sibling P1 envelope-layer on sys.path,
    resolved from this file's location, so the suites run from any
    working directory (laptop or S24) — not only from the repo root.
    Fixes NOTES.md D8 for the test runs; no layer code is changed.

Layer:    P4 — Ledger (test support)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ENVELOPE = os.path.join(os.path.dirname(_HERE), "envelope-layer")


# ---------------------------------------------------------------------------
# 1. _add_path
#    Prepend a directory to sys.path once.
# ---------------------------------------------------------------------------
def _add_path(path):
    if path not in sys.path:
        sys.path.insert(0, path)


_add_path(_ENVELOPE)
_add_path(_HERE)
