from __future__ import annotations

import json
from typing import Any

MOJIBAKE_MARKERS = ("Ð", "Ñ", "â€", "â", "Â")


def looks_like_mojibake(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    return any(marker in value for marker in MOJIBAKE_MARKERS)


def fix_mojibake_text(value: Any) -> Any:
    if not isinstance(value, str) or not value or not looks_like_mojibake(value):
        return value

    candidates = [value]
    for encoding in ("latin1", "cp1252"):
        try:
            candidates.append(value.encode(encoding).decode("utf-8"))
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue

    return min(candidates, key=_mojibake_score)


def clean_text_value(value: Any) -> Any:
    if isinstance(value, str):
        return fix_mojibake_text(value)
    if isinstance(value, list):
        return [clean_text_value(item) for item in value]
    if isinstance(value, dict):
        return {key: clean_text_value(item) for key, item in value.items()}
    return value


def clean_json_text(value: Any) -> Any:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return fix_mojibake_text(value)
        return clean_text_value(parsed)
    return clean_text_value(value)


def _mojibake_score(value: str) -> int:
    return sum(value.count(marker) for marker in MOJIBAKE_MARKERS)
