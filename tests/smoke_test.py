#!/usr/bin/env python3
"""End-to-end smoke tests for the portable journal-ranking Skill."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUERY_SCRIPT = ROOT / "scripts" / "query_journal.py"
EXPECTED_SOURCES = {
    "jcr2025": 22643,
    "emerging2026": 22299,
    "ssci2026": 3537,
    "ccf2026": 295,
    "ccft2025": 68,
    "fms-zh2025": 94,
    "fms-en2025": 1183,
    "cssci2025-2026": 674,
}


def query(*arguments: str, expected_exit: int = 0) -> dict:
    completed = subprocess.run(
        [sys.executable, str(QUERY_SCRIPT), *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != expected_exit:
        raise AssertionError(
            f"Query {arguments!r} exited {completed.returncode}, expected {expected_exit}: "
            f"{completed.stderr or completed.stdout}"
        )
    return json.loads(completed.stdout)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    about = query("--about")
    source_counts = {item["source_key"]: item["row_count"] for item in about["sources"]}
    check(source_counts == EXPECTED_SOURCES, "Bundled source editions or row counts changed")
    check(not any("fqbjcr" in key.casefold() for key in source_counts), "CAS partition source must be excluded")
    print("[OK] source metadata and CAS exclusion")

    finance = query("Journal of Finance")
    check(finance["match"]["status"] == "exact", "Journal of Finance must match exactly")
    finance_rankings = finance["result"]["rankings"]
    check(finance_rankings["jcr"]["impact_factor"]["display"] == "12.2", "Unexpected JCR IF")
    check(finance_rankings["ssci"]["status"] == "listed", "Expected SSCI listing")
    check(finance_rankings["fms"]["records"][0]["rating"] == "A", "Expected FMS A")
    print("[OK] English title exact lookup")

    management = query("管理世界")
    check(management["match"]["status"] == "exact", "管理世界 must match exactly")
    management_rankings = management["result"]["rankings"]
    check(management_rankings["fms"]["records"][0]["rating"] == "T1", "Expected FMS T1")
    check(management_rankings["cssci"]["status"] == "listed", "Expected CSSCI listing")
    print("[OK] Chinese title exact lookup")

    jacm = query("JACM")
    check(jacm["match"]["status"] == "exact", "JACM must match exactly")
    ccf_records = jacm["result"]["rankings"]["ccf"]["international"]
    check(ccf_records and ccf_records[0]["rating"] == "A类", "Expected CCF A rating")
    print("[OK] abbreviation and CCF lookup")

    fuzzy = query("Journal of Financal Economics")
    check(fuzzy["match"]["status"] == "fuzzy_candidates", "Misspelling must return fuzzy candidates")
    check(fuzzy["match"]["rankings_withheld_until_selection"] is True, "Fuzzy rankings must be withheld")
    check(fuzzy["candidates"][0]["canonical_name"] == "JOURNAL OF FINANCIAL ECONOMICS", "Unexpected top fuzzy candidate")
    print("[OK] fuzzy discovery without auto-selection")

    ambiguous = query("HEART RHYTHM")
    check(ambiguous["match"]["status"] == "ambiguous", "Duplicate title must be ambiguous")
    check(ambiguous["match"]["candidate_count"] == 2, "Expected two HEART RHYTHM candidates")
    check(ambiguous["match"]["rankings_withheld_until_selection"] is True, "Ambiguous rankings must be withheld")
    print("[OK] exact-title ambiguity protection")

    print("All 6 smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
