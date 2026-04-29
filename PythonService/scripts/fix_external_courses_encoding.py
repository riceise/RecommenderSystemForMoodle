from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.postgres_provider import PostgresDataProvider
from utils.text_encoding import clean_json_text, clean_text_value, fix_mojibake_text, looks_like_mojibake


def main() -> int:
    parser = argparse.ArgumentParser(description="Fix mojibake text in ExternalCourses.")
    parser.add_argument("--apply", action="store_true", help="Persist fixes to the database.")
    parser.add_argument("--limit", type=int, default=0, help="Optional max rows to inspect.")
    args = parser.parse_args()

    provider = PostgresDataProvider()
    rows = _load_rows(provider, args.limit)
    fixes = [_build_fix(row) for row in rows]
    fixes = [fix for fix in fixes if fix is not None]

    print(f"Found {len(fixes)} ExternalCourses rows with mojibake text.")
    for fix in fixes[:10]:
        print(f"- {fix['Id']}")
        print(f"  title: {fix['old_title']} -> {fix['Title']}")
        print(f"  description: {fix['old_description'][:140]} -> {fix['Description'][:140]}")

    if not args.apply:
        print("Dry run only. Re-run with --apply to update rows.")
        return 0

    _apply_fixes(provider, fixes)
    print(f"Updated {len(fixes)} rows.")
    return 0


def _load_rows(provider: PostgresDataProvider, limit: int) -> list[dict]:
    limit_sql = "LIMIT :limit" if limit and limit > 0 else ""
    query = text(f'''
        SELECT "Id", "Title", "Description", "Platform", "Topics", "SearchQuery", "MetadataJson"
        FROM "ExternalCourses"
        WHERE "IsActive" = true
          AND (
            "Title" LIKE '%Ð%' OR "Title" LIKE '%Ñ%' OR "Title" LIKE '%â€%' OR "Title" LIKE '%â%' OR "Title" LIKE '%Â%'
            OR "Description" LIKE '%Ð%' OR "Description" LIKE '%Ñ%' OR "Description" LIKE '%â€%' OR "Description" LIKE '%â%' OR "Description" LIKE '%Â%'
            OR "Platform" LIKE '%Ð%' OR "Platform" LIKE '%Ñ%' OR "Platform" LIKE '%â€%' OR "Platform" LIKE '%â%' OR "Platform" LIKE '%Â%'
            OR "SearchQuery" LIKE '%Ð%' OR "SearchQuery" LIKE '%Ñ%' OR "SearchQuery" LIKE '%â€%' OR "SearchQuery" LIKE '%â%' OR "SearchQuery" LIKE '%Â%'
            OR "Topics"::text LIKE '%Ð%' OR "Topics"::text LIKE '%Ñ%' OR "Topics"::text LIKE '%â€%' OR "Topics"::text LIKE '%â%' OR "Topics"::text LIKE '%Â%'
            OR "MetadataJson" LIKE '%Ð%' OR "MetadataJson" LIKE '%Ñ%' OR "MetadataJson" LIKE '%â€%' OR "MetadataJson" LIKE '%â%' OR "MetadataJson" LIKE '%Â%'
          )
        ORDER BY "UpdatedAt" DESC
        {limit_sql}
    ''')
    params = {"limit": limit} if limit and limit > 0 else {}
    with provider.engine.connect() as connection:
        return [dict(row) for row in connection.execute(query, params).mappings().all()]


def _build_fix(row: dict) -> dict | None:
    fixed_topics = clean_text_value(row.get("Topics") or [])
    fixed_metadata = clean_json_text(row.get("MetadataJson") or {})
    fixed = {
        "Id": row["Id"],
        "Title": fix_mojibake_text(row.get("Title", "")),
        "Description": fix_mojibake_text(row.get("Description", "")),
        "Platform": fix_mojibake_text(row.get("Platform", "")),
        "Topics": fixed_topics,
        "SearchQuery": fix_mojibake_text(row.get("SearchQuery", "")),
        "MetadataJson": fixed_metadata,
        "old_title": row.get("Title", ""),
        "old_description": row.get("Description", ""),
    }
    changed = (
        fixed["Title"] != row.get("Title", "")
        or fixed["Description"] != row.get("Description", "")
        or fixed["Platform"] != row.get("Platform", "")
        or fixed["Topics"] != (row.get("Topics") or [])
        or fixed["SearchQuery"] != row.get("SearchQuery", "")
        or _metadata_changed(row.get("MetadataJson"), fixed_metadata)
    )
    if not changed and not any(looks_like_mojibake(row.get(field, "")) for field in ("Title", "Description", "Platform", "SearchQuery")):
        return None
    return fixed


def _metadata_changed(original: object, fixed: object) -> bool:
    try:
        original_obj = json.loads(original) if isinstance(original, str) else original
    except json.JSONDecodeError:
        original_obj = original
    return original_obj != fixed


def _apply_fixes(provider: PostgresDataProvider, fixes: list[dict]) -> None:
    if not fixes:
        return
    update_sql = text('''
        UPDATE "ExternalCourses"
        SET "Title" = :title,
            "Description" = :description,
            "Platform" = :platform,
            "Topics" = CAST(:topics AS jsonb),
            "SearchQuery" = :search_query,
            "MetadataJson" = :metadata_json,
            "UpdatedAt" = NOW()
        WHERE "Id" = :id
    ''')
    with provider.engine.begin() as connection:
        for fix in fixes:
            connection.execute(update_sql, {
                "id": fix["Id"],
                "title": fix["Title"],
                "description": fix["Description"],
                "platform": fix["Platform"],
                "topics": json.dumps(fix["Topics"], ensure_ascii=False),
                "search_query": fix["SearchQuery"],
                "metadata_json": json.dumps(fix["MetadataJson"], ensure_ascii=False),
            })


if __name__ == "__main__":
    raise SystemExit(main())
