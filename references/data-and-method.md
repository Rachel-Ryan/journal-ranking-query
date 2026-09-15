# Data and Method Reference

## Bundled latest editions

| Output group | Edition | Included records | Bundled source |
|---|---:|---:|---|
| JCR | 2025 | 22,643 journals | `JCR2025-UTF8.csv` |
| 新锐期刊分区 | 2026 | 22,299 records | `XR2026-UTF8.csv` |
| SSCI | 2026 | 3,537 journals | `SSCI-2026.xls` |
| CCF international journals | 2026 | 295 records | `CCF2026-UTF8.csv` |
| CCF Chinese technology journals | 2025 | 68 records | `CCFT2025-UTF8.csv` |
| FMS Chinese journals | 2025 | 94 records | `FMS中文期刊.xlsx` |
| FMS English journals | 2025 | 1,183 records | `FMS英文期刊.xlsx` |
| CSSCI source journals | 2025-2026 | 674 journals | `CSSCI-2026.md` |

The SQLite snapshot stores a SHA-256 checksum for every source. Run `query_journal.py --about` to retrieve the exact checksums.

The 2025 CAS/中科院分区 source is deliberately excluded from the database, output schema, and matching results.

## Output semantics

The top-level `match.status` controls whether rankings may be reported:

- `exact`: one entity matched through a serial identifier, folded title, or compact normalized title.
- `ambiguous`: multiple entities share the exact normalized input; rankings are withheld.
- `fuzzy_candidates`: approximate candidates only; rankings are withheld.
- `not_found`: no accepted candidate.
- `selected_entity`: a candidate was retrieved by its stable `entity_id`.

For a confirmed match, `result.rankings` always contains these keys: `jcr`, `ssci`, `emerging`, `ccf`, `fms`, and `cssci`. Each group gives `listed` or `not_listed`; CCF gives one overall status and separate `international` and `chinese_technology` arrays.

JCR `impact_factor.display` is the authoritative printable value. `impact_factor.value` is numeric only when the source contains an ordinary number. A source value such as `<0.1` additionally has `qualifier: less_than` and a threshold; `N/A` has a null numeric value.

## SSCI interpretation

SSCI membership is determined only from the 2026 SSCI list. SSCI categories are then matched to the same journal's JCR 2025 category names to expose category quartile and rank. This avoids treating the broader JCR journal universe as the current SSCI list.

Category matching is exact after punctuation/case normalization, with one explicit source-name alias: `Psychology, Development` maps to JCR's `Psychology, Developmental`. No semantic or fuzzy category inference is used. If an SSCI category has no JCR 2025 counterpart, the record keeps null values and reports `jcr_category_unavailable`; if the journal itself has no JCR 2025 record, it reports `jcr_record_unavailable`.

## Entity resolution and title matching

Cross-source entities are merged only by a unique ISSN/eISSN, or by a unique exact normalized title when the incoming source has no serial identifier. CN numbers are retained as identifiers but are not used as cross-database serial equivalents. Fuzzy similarity never merges source records.

Runtime lookup precedence is:

1. Exact ISSN/eISSN/CN after removing punctuation and normalizing case.
2. Unicode NFKC plus case-folded exact title/abbreviation/former-title match.
3. Exact compact title match after removing punctuation and whitespace.
4. Character-trigram shortlist followed by deterministic sequence, token, and trigram scoring.

If an exact normalized value maps to several entities, the script returns all candidates and withholds rankings. Fuzzy matching also returns identities only. This is intentional: similarity helps discover the title but never substitutes for identity confirmation.
