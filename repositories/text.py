from __future__ import annotations

import unicodedata


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()
