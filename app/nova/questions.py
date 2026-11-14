"""NOVA's daily check-in questions (fixed text, works offline)."""

QUESTIONS = {
    "sleep_hours": "About how many hours did you sleep last night?",
    "fatigue": "From 1 to 5, how tired do you feel right now?",
    "mood": "How is your mood today: good, okay, or not good?",
    "stress": "From 1 to 5, what is your stress level?",
}

FOLLOW_UPS = {
    "sleep_hours": "Could you give me a number of hours, even a rough one?",
    "fatigue": "Could you pick a number from 1 (not tired) to 5 (very tired)?",
    "mood": "Would you say good, okay, or not good?",
    "stress": "Could you pick a number from 1 (calm) to 5 (very stressed)?",
}


def missing_fields(answers: dict) -> list[str]:
    """Fields NOVA still needs to ask about (None means not answered)."""
    return [k for k in QUESTIONS if answers.get(k) is None]


def next_question(answers: dict, asked_once: set[str] | None = None) -> str | None:
    """Return the next thing NOVA should say, or None when all four are known."""
    asked_once = asked_once or set()
    for field in missing_fields(answers):
        return FOLLOW_UPS[field] if field in asked_once else QUESTIONS[field]
    return None


# Ring version: the ring measures sleep and body signs, so NOVA asks ONE spoken
# question at breakfast about what the ring can't measure (mood, stress, tiredness).
MORNING = {
    "en": "Good morning. How did you sleep, and how are you feeling today?",
    "ar": "صباح الخير. كيف كان نومك، وكيف تحس اليوم؟",
}
LOW_CONFIDENCE = {
    "en": "The ring data looks unusual today. From 1 to 5, how tired do you feel?",
    "ar": "بيانات الخاتم غير معتادة اليوم. من 1 إلى 5، كم تحس بالتعب؟",
}
