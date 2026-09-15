#!/usr/bin/env python3
"""Deterministic offline lookup for the bundled journal-ranking index."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
import zlib
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
DEFAULT_DB = Path(__file__).resolve().parents[1] / "assets" / "journal_rankings.sqlite3"


def clean(value: str) -> str:
    return " ".join(str(value).strip().split())


def folded_name(value: str) -> str:
    text = unicodedata.normalize("NFKC", clean(value)).casefold()
    text = text.replace("‐", "-").replace("‑", "-").replace("–", "-").replace("—", "-")
    return " ".join(text.split())


def compact_name(value: str) -> str:
    return "".join(character for character in folded_name(value) if character.isalnum())


def normalized_identifier(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKC", clean(value)).upper()
        if character.isalnum()
    )


def grams(value: str) -> set[str]:
    if not value:
        return set()
    padded = f"^{value}$"
    size = 3 if len(value) >= 3 else max(1, len(value))
    return {
        f"{size}:{padded[index:index + size]}"
        for index in range(max(1, len(padded) - size + 1))
    }


def connect_database(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(f"Ranking database not found: {path}")
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    version_row = connection.execute(
        "SELECT value FROM metadata WHERE key = 'schema_version'"
    ).fetchone()
    if not version_row or version_row["value"] != SCHEMA_VERSION:
        found = version_row["value"] if version_row else "missing"
        raise RuntimeError(f"Unsupported database schema: {found}")
    return connection


def load_payload(connection: sqlite3.Connection, entity_id: int) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT payload_zlib FROM entities WHERE entity_id = ?", (entity_id,)
    ).fetchone()
    if not row:
        return None
    return json.loads(zlib.decompress(row["payload_zlib"]).decode("utf-8"))


def candidate_identity(
    connection: sqlite3.Connection,
    entity_id: int,
    matched_aliases: list[dict[str, Any]] | None = None,
    score: float | None = None,
) -> dict[str, Any]:
    payload = load_payload(connection, entity_id)
    if payload is None:
        raise RuntimeError(f"Entity {entity_id} is missing")
    result: dict[str, Any] = {
        "entity_id": entity_id,
        "canonical_name": payload["canonical_name"],
        "identifiers": payload["identifiers"],
        "data_sources": payload["data_sources"],
    }
    if score is not None:
        result["score"] = score
    if matched_aliases:
        result["matched_aliases"] = matched_aliases
    result["selection_arguments"] = ["--entity-id", str(entity_id)]
    return result


def exact_matches(
    connection: sqlite3.Connection, query: str
) -> tuple[str | None, dict[int, list[dict[str, Any]]]]:
    identifier = normalized_identifier(query)
    if identifier:
        rows = connection.execute(
            """
            SELECT entity_id, kind, value, source_key
            FROM identifiers
            WHERE normalized = ?
            ORDER BY entity_id, kind, value, source_key
            """,
            (identifier,),
        ).fetchall()
        if rows:
            matches: dict[int, list[dict[str, Any]]] = {}
            for row in rows:
                matches.setdefault(row["entity_id"], []).append(
                    {
                        "value": row["value"],
                        "type": row["kind"],
                        "source": row["source_key"],
                    }
                )
            return "identifier_exact", matches

    folded = folded_name(query)
    rows = connection.execute(
        """
        SELECT entity_id, alias, alias_type, source_key
        FROM aliases
        WHERE alias_folded = ?
        ORDER BY entity_id, alias, alias_type, source_key
        """,
        (folded,),
    ).fetchall()
    if rows:
        matches = {}
        for row in rows:
            matches.setdefault(row["entity_id"], []).append(
                {
                    "value": row["alias"],
                    "type": row["alias_type"],
                    "source": row["source_key"],
                }
            )
        return "title_exact", matches

    compact = compact_name(query)
    if compact:
        rows = connection.execute(
            """
            SELECT entity_id, alias, alias_type, source_key
            FROM aliases
            WHERE alias_compact = ?
            ORDER BY entity_id, alias, alias_type, source_key
            """,
            (compact,),
        ).fetchall()
        if rows:
            matches = {}
            for row in rows:
                matches.setdefault(row["entity_id"], []).append(
                    {
                        "value": row["alias"],
                        "type": row["alias_type"],
                        "source": row["source_key"],
                    }
                )
            return "title_normalized_exact", matches
    return None, {}


def ratio(left: str, right: str) -> float:
    return SequenceMatcher(None, left, right, autojunk=False).ratio()


def token_sort(value: str) -> str:
    return " ".join(sorted(re.findall(r"\w+", value, flags=re.UNICODE)))


def fuzzy_score(query_folded: str, query_compact: str, alias_folded: str, alias_compact: str,
                overlap: int, query_gram_count: int, alias_gram_count: int) -> float:
    sequence = ratio(query_compact, alias_compact)
    token = ratio(token_sort(query_folded), token_sort(alias_folded))
    denominator = query_gram_count + alias_gram_count
    dice = (2.0 * overlap / denominator) if denominator else 0.0
    score = 100.0 * (0.60 * sequence + 0.30 * dice + 0.10 * token)
    if query_compact in alias_compact or alias_compact in query_compact:
        containment = 100.0 * min(len(query_compact), len(alias_compact)) / max(
            len(query_compact), len(alias_compact)
        )
        score = max(score, containment)
    return round(score, 2)


def fuzzy_matches(
    connection: sqlite3.Connection, query: str, limit: int, min_score: float
) -> list[dict[str, Any]]:
    query_folded = folded_name(query)
    query_compact = compact_name(query)[:256]
    if len(query_compact) < 2:
        return []
    query_grams = sorted(grams(query_compact))
    placeholders = ",".join("?" for _ in query_grams)
    rows = connection.execute(
        f"""
        SELECT a.alias_id, a.entity_id, a.alias, a.alias_folded, a.alias_compact,
               a.alias_type, a.source_key, a.gram_count, COUNT(*) AS overlap
        FROM alias_grams AS g
        JOIN aliases AS a ON a.alias_id = g.alias_id
        WHERE g.gram IN ({placeholders})
        GROUP BY a.alias_id
        ORDER BY overlap DESC, a.alias_id
        LIMIT 800
        """,
        query_grams,
    ).fetchall()

    best_by_entity: dict[int, dict[str, Any]] = {}
    for row in rows:
        score = fuzzy_score(
            query_folded,
            query_compact,
            row["alias_folded"],
            row["alias_compact"],
            row["overlap"],
            len(query_grams),
            row["gram_count"],
        )
        if score < min_score:
            continue
        match = {
            "value": row["alias"],
            "type": row["alias_type"],
            "source": row["source_key"],
        }
        candidate = {
            "entity_id": row["entity_id"],
            "score": score,
            "matched_aliases": [match],
        }
        current = best_by_entity.get(row["entity_id"])
        if current is None or (
            score,
            folded_name(row["alias"]),
            row["alias_type"],
            row["source_key"],
        ) > (
            current["score"],
            folded_name(current["matched_aliases"][0]["value"]),
            current["matched_aliases"][0]["type"],
            current["matched_aliases"][0]["source"],
        ):
            best_by_entity[row["entity_id"]] = candidate

    scored = []
    for candidate in best_by_entity.values():
        identity = candidate_identity(
            connection,
            candidate["entity_id"],
            candidate["matched_aliases"],
            candidate["score"],
        )
        scored.append(identity)
    scored.sort(key=lambda item: (-item["score"], folded_name(item["canonical_name"]), item["entity_id"]))
    return scored[:limit]


def about(connection: sqlite3.Connection) -> dict[str, Any]:
    metadata = {
        row["key"]: row["value"]
        for row in connection.execute("SELECT key, value FROM metadata ORDER BY key")
    }
    sources = [
        dict(row)
        for row in connection.execute(
            """
            SELECT source_key, label, edition, file_name, sha256, row_count
            FROM sources
            ORDER BY source_key
            """
        )
    ]
    return {"schema_version": SCHEMA_VERSION, "metadata": metadata, "sources": sources}


def perform_query(
    connection: sqlite3.Connection,
    query: str,
    mode: str,
    limit: int,
    min_score: float,
) -> tuple[dict[str, Any], int]:
    base: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "query": {"input": query, "mode": mode},
    }
    strategy, matches = exact_matches(connection, query)
    if matches:
        entity_ids = sorted(matches)
        if len(entity_ids) == 1:
            entity_id = entity_ids[0]
            base["match"] = {
                "status": "exact",
                "strategy": strategy,
                "candidate_count": 1,
                "matched_values": matches[entity_id],
            }
            base["result"] = load_payload(connection, entity_id)
            return base, 0
        base["match"] = {
            "status": "ambiguous",
            "strategy": strategy,
            "candidate_count": len(entity_ids),
            "rankings_withheld_until_selection": True,
        }
        base["candidates"] = [
            candidate_identity(connection, entity_id, matches[entity_id])
            for entity_id in entity_ids
        ]
        return base, 0

    if mode == "exact":
        base["match"] = {"status": "not_found", "strategy": "exact_only", "candidate_count": 0}
        return base, 1

    candidates = fuzzy_matches(connection, query, limit, min_score)
    if candidates:
        base["match"] = {
            "status": "fuzzy_candidates",
            "strategy": "normalized_trigram_similarity",
            "candidate_count": len(candidates),
            "rankings_withheld_until_selection": True,
        }
        base["candidates"] = candidates
        return base, 0
    base["match"] = {
        "status": "not_found",
        "strategy": "fuzzy",
        "candidate_count": 0,
        "reason": "No candidate met the similarity threshold",
    }
    return base, 1


def render_text(document: dict[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=False, indent=2, sort_keys=False)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Query the bundled latest-edition journal ranking data."
    )
    parser.add_argument("query", nargs="?", help="Journal title, abbreviation, former title, ISSN, eISSN, or CN")
    parser.add_argument("--mode", choices=("auto", "exact", "fuzzy"), default="auto")
    parser.add_argument("--limit", type=int, default=5, help="Maximum fuzzy candidates (1-20)")
    parser.add_argument("--min-score", type=float, default=60.0, help="Minimum fuzzy score (0-100)")
    parser.add_argument("--entity-id", type=int, help="Return a previously selected entity")
    parser.add_argument("--about", action="store_true", help="Show bundled source editions and checksums")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args()

    if not 1 <= args.limit <= 20:
        parser.error("--limit must be between 1 and 20")
    if not 0 <= args.min_score <= 100:
        parser.error("--min-score must be between 0 and 100")

    try:
        connection = connect_database(DEFAULT_DB)
        if args.about:
            document = about(connection)
            exit_code = 0
        elif args.entity_id is not None:
            payload = load_payload(connection, args.entity_id)
            if payload is None:
                document = {
                    "schema_version": SCHEMA_VERSION,
                    "match": {"status": "not_found", "strategy": "entity_id", "entity_id": args.entity_id},
                }
                exit_code = 1
            else:
                document = {
                    "schema_version": SCHEMA_VERSION,
                    "match": {"status": "selected_entity", "strategy": "entity_id", "entity_id": args.entity_id},
                    "result": payload,
                }
                exit_code = 0
        else:
            query = clean(args.query or "")
            if not query:
                parser.error("a query is required unless --about or --entity-id is used")
            document, exit_code = perform_query(
                connection, query, args.mode, args.limit, args.min_score
            )
        connection.close()
        output = (
            json.dumps(document, ensure_ascii=False, separators=(",", ":"))
            if args.format == "json"
            else render_text(document)
        )
        print(output)
        return exit_code
    except (FileNotFoundError, RuntimeError, sqlite3.Error, zlib.error, json.JSONDecodeError) as error:
        print(
            json.dumps(
                {"schema_version": SCHEMA_VERSION, "error": str(error)},
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
