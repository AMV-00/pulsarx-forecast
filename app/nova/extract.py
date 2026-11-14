"""Turn the astronaut's free text into four fields.

Claude only reads and labels the text. It never makes up a value:
anything not clearly said stays None, and NOVA asks again.
If the API is not reachable, a simple offline parser is used.
"""
import re

FIELDS = ("sleep_hours", "fatigue", "mood", "stress")
MOODS = ("good", "okay", "bad")

EXTRACT_TOOL = {
    "name": "record_checkin",
    "description": "Record only what the astronaut clearly said. Use null for anything not stated.",
    "input_schema": {
        "type": "object",
        "properties": {
            "sleep_hours": {"type": ["number", "null"], "description": "Hours slept last night, 0-14."},
            "fatigue": {"type": ["integer", "null"], "description": "1 (not tired) to 5 (very tired)."},
            "mood": {"type": ["string", "null"], "enum": ["good", "okay", "bad", None]},
            "stress": {"type": ["integer", "null"], "description": "1 (calm) to 5 (very stressed)."},
            "hedging": {
                "type": "boolean",
                "description": "True if answers sound evasive, very short, or play down tiredness (e.g. 'fine I guess').",
            },
        },
        "required": ["sleep_hours", "fatigue", "mood", "stress", "hedging"],
    },
}

SYSTEM = (
    "You are NOVA, a check-in assistant for astronauts. Extract sleep hours, fatigue (1-5), "
    "mood (good/okay/bad) and stress (1-5) from what the astronaut wrote. "
    "Only record values the astronaut actually stated or clearly implied. Never guess a number: use null. "
    "Do not diagnose anything."
)


def _clean(raw: dict) -> dict:
    """Keep values inside valid ranges; anything else becomes None."""
    out = {k: raw.get(k) for k in FIELDS}
    s = out["sleep_hours"]
    out["sleep_hours"] = float(s) if isinstance(s, (int, float)) and 0 <= s <= 14 else None
    for k in ("fatigue", "stress"):
        v = out[k]
        out[k] = int(v) if isinstance(v, (int, float)) and 1 <= v <= 5 else None
    out["mood"] = out["mood"] if out["mood"] in MOODS else None
    out["hedging"] = bool(raw.get("hedging", False))
    return out


def extract_with_claude(text: str, client=None, model: str = "claude-sonnet-5-5") -> dict:
    if client is None:
        from anthropic import Anthropic
        from dotenv import load_dotenv

        load_dotenv()
        client = Anthropic()
    msg = client.messages.create(
        model=model,
        max_tokens=300,
        system=SYSTEM,
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "record_checkin"},
        messages=[{"role": "user", "content": text}],
    )
    for block in msg.content:
        if block.type == "tool_use":
            return _clean(block.input)
    return _clean({})


_HEDGES = ("i guess", "fine", "whatever", "not sure", "ok i think", "dunno")


def extract_offline(text: str) -> dict:
    """Very simple keyword parser used when there is no internet."""
    t = text.lower()
    raw: dict = {}
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:h|hr|hrs|hour|hours)\b", t)
    if m:
        raw["sleep_hours"] = float(m.group(1))
    m = re.search(r"(?:tired|fatigue)\D{0,15}([1-5])\b", t)
    if m:
        raw["fatigue"] = int(m.group(1))
    m = re.search(r"stress\D{0,15}([1-5])\b", t)
    if m:
        raw["stress"] = int(m.group(1))
    if re.search(r"not good|bad|sad|down|low", t):
        raw["mood"] = "bad"
    elif re.search(r"\bgood\b|great|happy", t):
        raw["mood"] = "good"
    elif re.search(r"\bokay\b|\bok\b|normal", t):
        raw["mood"] = "okay"
    raw["hedging"] = len(t.split()) < 4 or any(h in t for h in _HEDGES)
    return _clean(raw)


def extract(text: str, client=None) -> dict:
    """Try Claude first, fall back to the offline parser. Adds 'source'."""
    try:
        result = extract_with_claude(text, client=client)
        result["source"] = "claude"
    except Exception:
        result = extract_offline(text)
        result["source"] = "offline"
    return result
