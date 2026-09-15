---
name: journal-ranking-query
description: Deterministically query the bundled latest-edition journal data for JCR quartiles and impact factor, emerging-journal quartiles, SSCI membership and category quartiles, CCF international and Chinese-technology ratings, FMS ratings, and CSSCI status. Use when a user gives a journal title, abbreviation, former title, ISSN, eISSN, or CN number and asks about 期刊级别、期刊等级、JCR、影响因子、新锐分区、SSCI、CCF、FMS or CSSCI. Supports exact lookup, normalized lookup, and fuzzy candidate discovery.
metadata:
  version: "1.0.0"
  data-as-of: "2026-09-15"
---

# Journal Ranking Query

Use the bundled script for every lookup. Do not manually search the SQLite file or infer a ranking from the journal name.

This skill requires a local shell and Python 3.8 or newer. It runs fully offline with Python standard library only.

## Run a lookup

1. Resolve this skill's directory: it is the directory containing this `SKILL.md`.
2. Use an available Python 3 launcher (`python3`, then `python`; on Windows, `py -3` is also acceptable).
3. Pass the user's complete journal input as one quoted argument:

```bash
python3 "<skill-directory>/scripts/query_journal.py" "<journal title, abbreviation, former title, ISSN, eISSN, or CN>"
```

The default `auto` mode tries identifier and title exact matching first, then fuzzy discovery. Use `--mode exact` only when the user explicitly rejects fuzzy matching. Use `--mode fuzzy` to request candidates after an unsuccessful exact lookup.

## Handle the result

Follow `match.status` exactly:

- `exact`: Report `result`. Include every returned category and record rather than collapsing to one quartile or one discipline.
- `ambiguous`: Do not report any candidate's rankings as the answer. Show the candidate names and identifiers, then ask the user to select one.
- `fuzzy_candidates`: Explain that these are candidates, not confirmed matches. Do not silently choose the first result, even when its score is highest.
- `not_found`: State that no match was found in the bundled lists. Do not interpret this as a quality judgment.
- `selected_entity`: Report `result` after a user selection.

To retrieve a selected candidate, reuse its `selection_arguments`:

```bash
python3 "<skill-directory>/scripts/query_journal.py" --entity-id <id>
```

## Report all requested dimensions

For a confirmed entity, cover every requested dimension in `result.rankings`:

1. JCR 2025: impact factor plus every JCR category, quartile, and rank.
2. SSCI 2026: current membership plus every SSCI category and its mapped JCR 2025 quartile/rank when available.
3. 新锐期刊分区 2026: every broad and subject category, including Top/warning/annotation fields when present.
4. CCF: keep `international` A/B/C and `chinese_technology` T1/T2/T3 separate; never combine them into one grade.
5. FMS 2025: return all Chinese or English list records and their grades.
6. CSSCI 2025-2026: report source-journal status and discipline.
7. Explicitly distinguish `listed` from `not_listed` for every group.

Do not add or report any 2025 CAS/中科院分区 data. It is intentionally absent from this skill.

## Interpretation rules

- `not_listed` means absent from that bundled latest-edition list, not “unrecognized everywhere” and not “low quality.”
- Preserve impact-factor display values such as `<0.1` or `N/A`; do not turn them into invented point estimates.
- SSCI status comes from the 2026 SSCI list. Its category quartiles are mapped only to same-journal JCR 2025 categories; a null quartile with `jcr_category_unavailable` is a valid, explicit outcome.
- CCF 2026 data includes international journals only; conference rows were excluded during indexing.
- Fuzzy scores rank possible titles but do not prove identity. Confirmation requires the user to select a candidate or provide an identifier.
- Stay offline and use the bundled snapshot unless the user explicitly asks for an online or newer-source verification.

Read [references/data-and-method.md](references/data-and-method.md) when the user asks about editions, source provenance, matching rules, or field semantics. Read [references/installation.md](references/installation.md) when packaging or installing this skill on another Agent platform.

## Inspect provenance

Run this only when source editions or checksums are needed:

```bash
python3 "<skill-directory>/scripts/query_journal.py" --about --format text
```
