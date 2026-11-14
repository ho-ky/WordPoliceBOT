from functools import lru_cache
from threading import Lock
import unicodedata

from sudachipy import Dictionary

from repositories.text import normalize_text


_KANA_TABLE = {code: code - 96 for code in range(0x30A1, 0x30F7)}
_tokenizer = None
_tokenizer_lock = Lock()


def normalize_reading(value: str) -> str:
    return normalize_text(value).translate(_KANA_TABLE)


def validate_reading(value: str) -> str:
    reading = normalize_reading(value.strip())
    if not reading or any(
        not ("ぁ" <= character <= "ゖ" or character == "ー")
        for character in reading
    ):
        raise ValueError("読みはひらがなかカタカナで入力してください。")
    return reading


def message_reading(value: str) -> str:
    global _tokenizer
    text = normalize_text(value)
    if not any(
        character in "々〇〆"
        or unicodedata.name(character, "").startswith(("CJK UNIFIED IDEOGRAPH", "CJK COMPATIBILITY IDEOGRAPH"))
        for character in text
    ):
        return normalize_reading(text)

    with _tokenizer_lock:
        if _tokenizer is None:
            _tokenizer = Dictionary(dict="small").create()
        parts = []
        for token in _tokenizer.tokenize(text):
            surface = token.surface()
            parts.append(surface if surface.isascii() else token.reading_form() or surface)
    return normalize_reading("".join(parts))


@lru_cache(maxsize=2048)
def infer_watch_word_reading(word: str) -> str:
    return message_reading(word.strip())
