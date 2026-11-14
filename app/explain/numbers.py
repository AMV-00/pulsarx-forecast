"""Task 5 helper: make sure a sentence never invents numbers."""
import re

_NUM = re.compile(r"\d+(?:[.:]\d+)?")
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def numbers_in(text: str) -> set[str]:
    return set(_NUM.findall(text.translate(_AR_DIGITS)))


def numbers_ok(sentence: str, allowed: str | set[str]) -> bool:
    """True if every number in `sentence` also appears in `allowed`."""
    allowed_set = numbers_in(allowed) if isinstance(allowed, str) else set(allowed)
    return numbers_in(sentence) <= allowed_set
