"""Tests for the Dataset 3 district coverage / churn audit.

Run from project root:  .venv/bin/python -m pytest tests/recent_hmis -q
"""
import json
import os
import hashlib
import sys

import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
D3_DIR = os.path.join(ROOT, "data", "recent_hmis", "dataset3")
AUDIT = os.path.join(D3_DIR, "coverage_audit")
LIB = os.path.join(AUDIT, "_lib")
if LIB not in sys.path:
    sys.path.insert(0, LIB)

import audit_common as ac  # noqa: E402

ALLOWED_TYPES = {"EXACT", "FORMAT_VARIANT", "ALIAS_CANDIDATE",
                 "POSSIBLE_REORGANIZATION", "POSSIBLE_SPLIT", "POSSIBLE_MERGE", "UNCERTAIN"}
ALLOWED_ACTIONS = {"KEEP_SEPARATE", "INVESTIGATE", "POSSIBLE_MAPPING", "NO_MAPPING"}
CAND_SCHEMA = ["State", "Original_District", "Recent_HMIS_District", "Candidate_Type",
               "Confidence", "Evidence", "First_Historical_Year", "First_Recent_HMIS_Year",
               "Last_Recent_HMIS_Year", "Action"]


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="module")
def ref():
    return ac.load_reference()


@pytest.fixture(scope="module")
def ds3():
    return ac.load_ds3()


@pytest.fixture(scope="module")
def candidates():
    return pd.read_csv(os.path.join(AUDIT, "district_mapping_candidates.csv"), keep_default_na=False)


@pytest.fixture(scope="module")
def snapshot():
    return pd.read_csv(os.path.join(AUDIT, "reference_units_snapshot.csv"))


# --------------------------------------------------------------------------- #
# 1. dataset1.csv / dataset2.csv unchanged (read-only audit)
# --------------------------------------------------------------------------- #
def test_dataset1_2_unchanged():
    with open(os.path.join(D3_DIR, "_protected_files_baseline.json")) as fh:
        base = json.load(fh)["files"]
    for f in ["dataset1.csv", "dataset2.csv"]:
        assert _sha(os.path.join(ROOT, f)) == base[f], f"{f} changed by audit"


# --------------------------------------------------------------------------- #
# 2. Dataset 3 unchanged (read-only audit)
# --------------------------------------------------------------------------- #
def test_dataset3_unchanged():
    with open(os.path.join(AUDIT, "_audit_assets_baseline.json")) as fh:
        base = json.load(fh)["files"]
    assert base.get("data/recent_hmis/dataset3/dataset3_recent_hmis.csv") is not None
    changed = [f for f, h in base.items()
               if f.endswith("dataset3_recent_hmis.csv") and _sha(os.path.join(ROOT, f)) != h]
    assert not changed, "dataset3_recent_hmis.csv changed by audit"


# --------------------------------------------------------------------------- #
# 3. No automatic district merges performed / proposed
# --------------------------------------------------------------------------- #
def test_no_automatic_merges(candidates):
    assert set(candidates.columns) == set(CAND_SCHEMA), f"unexpected columns: {set(candidates.columns) ^ set(CAND_SCHEMA)}"
    assert set(candidates["Action"]) <= ALLOWED_ACTIONS, set(candidates["Action"]) - ALLOWED_ACTIONS
    assert set(candidates["Candidate_Type"]) <= ALLOWED_TYPES, set(candidates["Candidate_Type"]) - ALLOWED_TYPES
    assert not candidates["Action"].str.contains("MERGE", case=False, na=False).any(), \
        "no merge action may be proposed in the audit"
    assert not candidates["Action"].str.contains("AUTO", case=False, na=False).any(), \
        "no automatic action may be proposed"


# --------------------------------------------------------------------------- #
# 4. Every original 707 reference unit represented in the snapshot
# --------------------------------------------------------------------------- #
def test_all_707_reference_units_represented(snapshot):
    assert len(snapshot) == 707, f"reference snapshot has {len(snapshot)} rows, expected 707"
    assert (snapshot["Matched_Overall"] == "YES").all(), \
        snapshot[snapshot["Matched_Overall"] != "YES"]["District"].tolist()


# --------------------------------------------------------------------------- #
# 5. Every one of the 105 unmatched units is accounted for
# --------------------------------------------------------------------------- #
def test_all_105_unmatched_units_accounted_for(ref, ds3, candidates):
    ref_units = ac.reference_units(ref)
    ref_keys = {(sk, dk) for sk, m in ref_units.items() for dk in m}
    ds3_keys = {(r["Skey"], r["Dkey"]) for _, r in
                ds3.drop_duplicates(["State", "District"]).iterrows()}
    new_keys = set(ds3_keys) - ref_keys
    assert len(new_keys) == 105, f"{len(new_keys)} new units, expected 105"

    cand_pairs = {(ac.norm(r["State"]), ac.norm(r["Recent_HMIS_District"]))
                  for _, r in candidates.iterrows()}
    missing = sorted(str(k) for k in (new_keys - cand_pairs))
    extra = sorted(str(k) for k in (cand_pairs - new_keys))
    assert not missing, f"105-units missing from candidates: {missing}"
    assert not extra, f"candidate rows that are not new units (must be documented): {extra}"


# --------------------------------------------------------------------------- #
# 6. Every proposed candidate has an explicit evidence and action
# --------------------------------------------------------------------------- #
def test_every_candidate_has_evidence_and_action(candidates):
    assert len(candidates) == 105, f"expected 105 candidate rows, got {len(candidates)}"
    for col in ["Candidate_Type", "Confidence", "Evidence", "Action",
                "First_Recent_HMIS_Year", "Last_Recent_HMIS_Year"]:
        empty = candidates[candidates[col].astype(str).str.strip() == ""]
        assert len(empty) == 0, f"{col} empty for {empty['Recent_HMIS_District'].tolist()}"
    assert candidates["Confidence"].isin({"HIGH", "MEDIUM", "LOW"}).all()


# --------------------------------------------------------------------------- #
# Extra consistency: classification counts reconcile to 105; report exists
# --------------------------------------------------------------------------- #
def test_table_reconciliation(candidates):
    by_type = candidates["Candidate_Type"].value_counts().to_dict()
    assert sum(by_type.values()) == 105
    assert by_type.get("UNCERTAIN", 0) == 7
    assert by_type.get("FORMAT_VARIANT", 0) == 13
    assert by_type.get("ALIAS_CANDIDATE", 0) == 7
    assert by_type.get("POSSIBLE_SPLIT", 0) == 1
    assert by_type.get("POSSIBLE_REORGANIZATION", 0) == 77


def test_report_and_auxiliary_files_exist():
    for f in ["coverage_audit_report.md",
              "district_alias_candidates.csv",
              "district_reorganization_cases.csv",
              "external_verification_cases.csv",
              "district_signature_evidence.csv"]:
        assert os.path.exists(os.path.join(AUDIT, f)), f"missing audit artifact {f}"