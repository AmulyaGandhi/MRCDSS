"""Snapshot SHA-256 of all MRCDSS resources that Dataset 3 must NOT alter.

Writes data/recent_hmis/dataset3/_protected_files_baseline.json.
Used by tests/recent_hmis/test_unchanged.py to prove that the construction
phase did not modify: dataset1.csv, dataset2.csv, models/, outputs/, src/,
backend/, frontend/ sources, and the raw HMIS XLSX files.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
OUT_DIR = os.path.join(ROOT, "data", "recent_hmis", "dataset3")
OUT = os.path.join(OUT_DIR, "_protected_files_baseline.json")

TARGETS = [
    "dataset1.csv",
    "dataset2.csv",
    "models",
    "outputs",
    "src",
    "backend",
    "frontend",
    "config.yaml",
    "requirements.txt",
    "README.md",
    "verify_data.py",
    "correlation_check.py",
    "candidate_check.py",
    "final_feature_check.py",
    "data/recent_hmis/raw",
    "data/recent_hmis/inspection",
    "data/recent_hmis/fetch_hmis.py",
    "data/recent_hmis/acquisition_report.md",
]

SKIP_DIRS = {"node_modules", "__pycache__", ".git", "dataset3", ".venv"}
SKIP_SUFFIXES = (".pyc", ".pyo", ".DS_Store")


def _hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def walk(files):
    rel = os.path.relpath
    manifest = {}
    for t in TARGETS:
        p = os.path.join(ROOT, t)
        if os.path.isfile(p):
            files.append(rel(p, ROOT))
        elif os.path.isdir(p):
            for dirpath, dirnames, filenames in os.walk(p):
                dirnames[:] = [d for d in dirnames
                               if d not in SKIP_DIRS and not d.endswith(SKIP_SUFFIXES)]
                for fn in filenames:
                    if fn.endswith(SKIP_SUFFIXES):
                        continue
                    files.append(rel(os.path.join(dirpath, fn), ROOT))
    return files


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    files = walk([])
    manifest = {f: _hash_file(os.path.join(ROOT, f)) for f in sorted(files)}
    with open(OUT, "w") as fh:
        json.dump({"root": ROOT, "files": manifest}, fh, indent=1, sort_keys=True)
    print(f"snapshot: {len(manifest)} entries -> {OUT}")


if __name__ == "__main__":
    main()
    sys.exit(0)