import re

from app.fallback.answers import ANSWERS, answer


def test_same_keys_in_both_languages():
    assert ANSWERS["en"].keys() == ANSWERS["ar"].keys()


def test_fallback_answers_have_no_numbers():
    for lang in ANSWERS:
        for text in ANSWERS[lang].values():
            assert not re.search(r"[0-9٠-٩]", text), text


def test_unknown_key_is_safe():
    assert answer("nope", "ar") == ANSWERS["ar"]["unknown"]
