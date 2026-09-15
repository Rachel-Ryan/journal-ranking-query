# Journal Ranking Query Skill

[简体中文](README.md)

An offline Agent Skill for academic researchers. Given a journal title, abbreviation, former title, ISSN, eISSN, or CN number, it deterministically queries the latest bundled snapshot for JCR quartiles and impact factor, emerging-journal quartiles, SSCI, CCF, FMS, and CSSCI information.

This project is primarily intended for Chinese scholars, so Chinese documentation is provided first. It uses the open [Agent Skills](https://agentskills.io/) directory structure and supports at least Codex and Claude Code. Other Agent platforms can also use it if they can read `SKILL.md`, execute local Python, and retain the SQLite asset.

## Key Features

- Fully offline and depends only on the Python standard library.
- Supports exact lookup and fuzzy discovery by journal title, abbreviation, former title, ISSN, eISSN, and CN number.
- Returns all relevant quartiles while protecting against fuzzy-match and duplicate-title ambiguity.
- Keeps CCF International A/B/C ratings separate from Chinese technology journal T1/T2/T3 ratings.
- Queries only the latest snapshot from each source and excludes the 2025 CAS journal partition.

## Current Data Coverage

| Dataset | Edition | Records | Catalog Source |
|---|---:|---:|---|
| JCR journals, impact factors, and quartiles | 2025 | 22,643 | [ShowJCR](https://github.com/hitfyd/ShowJCR) |
| Emerging-journal quartiles | 2026 | 22,299 | [ShowJCR](https://github.com/hitfyd/ShowJCR) |
| SSCI journal list | 2026 | 3,537 | [Bohui Academic](http://www.upubfast.com/wos.html) |
| CCF recommended international academic journals | 2026 | 295 | [ShowJCR](https://github.com/hitfyd/ShowJCR) |
| CCF high-quality Chinese technology journals | 2025 | 68 | [ShowJCR](https://github.com/hitfyd/ShowJCR) |
| FMS Chinese journals | 2025 | 94 | [Official FMS Website](https://www.fms-journal.net/) |
| FMS English journals | 2025 | 1,183 | [Official FMS Website](https://www.fms-journal.net/) |
| CSSCI source journals | 2025–2026 | 674 | [University Library](https://lib.sdx.js.cn/col/col2622/index.html) |

SSCI inclusion is determined from the 2026 SSCI list. SSCI-category quartiles and ranks come from the corresponding JCR 2025 categories for the same journal. See [Data and Matching Method](references/data-and-method.md) for details.

## Let an Agent Install and Test It Automatically

Send the entire prompt below to Codex, Claude Code, or another Agent capable of local file and command execution. Replace the repository URL on the first line with your actual URL.

```text
Install and test the `journal-ranking-query` Skill from this repository:

Repository: <GitHub repository URL>

First read `README.md` and `SKILL.md` in the repository, then:
1. Detect the current Agent platform and install it in the user-level Skills directory: use `~/.codex/skills/journal-ranking-query` for Codex and `~/.claude/skills/journal-ranking-query` for Claude Code.
2. Confirm that Python ≥ 3.8 is available, then run `python3 tests/smoke_test.py` from the installed directory; use `python` or `py -3` instead if needed.
3. Report the installation path, Python version, and test result. If a test fails, explain why and make no unrelated changes.
```

## Manual Installation

Python 3.8 or newer is required. Keep the entire repository intact when installing; do not copy only `SKILL.md`.

### Codex

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL> ~/.codex/skills/journal-ranking-query
```

If `CODEX_HOME` is configured, install it under `skills/journal-ranking-query` within that directory.

### Claude Code

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL> ~/.claude/skills/journal-ranking-query
```

For a project-level installation, copy it to `<project-directory>/.claude/skills/journal-ranking-query`. Other Agent platforms should import the complete repository into their Skills directory and allow local Python execution.

## Test After Installation

```bash
python3 tests/smoke_test.py
```

The test checks data coverage, exact and fuzzy lookup, duplicate-title ambiguity, and exclusion of the CAS journal partition. You can also query directly:

```bash
python3 scripts/query_journal.py "Journal of Finance" --format text
```

## Query Result Conventions

The script outputs JSON by default. Only `exact` and `selected_entity` results may be reported directly. `ambiguous` and `fuzzy_candidates` require journal identity confirmation first. `not_found` or `not_listed` means only that the current snapshot has no corresponding record; it is not a judgment of journal quality.

## Data and Disclaimer

- This project is not an official product of Clarivate, SSCI, CCF, FMS, CSSCI, or the emerging-journal ranking provider.
- Results are provided only as a reference for research, journal selection, and information retrieval. Formal determinations should rely on the issuing organization's current publication.


## Acknowledgments

- [ShowJCR](https://github.com/hitfyd/ShowJCR): Some journal catalog data comes from this project;
- [2026 JCR Journal Quartile Query Website](https://brentnvp-art.github.io/jcr-query/): This project was inspired by it;
