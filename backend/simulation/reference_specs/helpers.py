from __future__ import annotations

import string

REGULAR_TILING_SOURCES = ("https://en.wikipedia.org/wiki/Regular_tiling",)


def _alphabetic_slots(count: int) -> tuple[str, ...]:
    values: list[str] = []
    index = 0
    alphabet = string.ascii_lowercase
    while len(values) < count:
        if index < len(alphabet):
            values.append(alphabet[index])
        else:
            high, low = divmod(index - len(alphabet), len(alphabet))
            values.append(alphabet[high] + alphabet[low])
        index += 1
    return tuple(sorted(values))


def _prefixed_slots(prefix: str, count: int) -> tuple[str, ...]:
    return tuple(sorted(f"{prefix}{index}" for index in range(count)))
