import re
from functools import lru_cache

# Базовый список для демонстрации; при необходимости расширьте или подключите внешний словарь.
PROFANITY_WORDS: frozenset[str] = frozenset(
    {
        "бля",
        "блять",
        "блядь",
        "сука",
        "суки",
        "хуй",
        "хуя",
        "хуе",
        "хуи",
        "пизда",
        "пиздец",
        "ебать",
        "ебал",
        "ебан",
        "ёб",
        "fuck",
        "fucking",
        "shit",
        "bitch",
        "asshole",
        "damn",
    }
)


@lru_cache(maxsize=1)
def _profanity_pattern() -> re.Pattern[str]:
    escaped = "|".join(re.escape(word) for word in sorted(PROFANITY_WORDS, key=len, reverse=True))
    # Границы слова: не буква/цифра до и после (поддержка кириллицы и латиницы).
    return re.compile(
        rf"(?<![\w\u0400-\u04FF])(?:{escaped})(?![\w\u0400-\u04FF])",
        re.IGNORECASE | re.UNICODE,
    )


def contains_profanity(text: str | None) -> bool:
    if not text or not text.strip():
        return False
    normalized = text.lower().strip()
    if _profanity_pattern().search(normalized):
        return True
    tokens = re.findall(r"[\w\u0400-\u04FF]+", normalized)
    return any(token in PROFANITY_WORDS for token in tokens)
