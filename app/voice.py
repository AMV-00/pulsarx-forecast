"""Voice tone check (experimental).

The browser measures four simple things while the astronaut talks to NOVA:
  speech_rate  words per minute
  pause_ratio  share of the time that is silence (0 to 1)
  pitch_var    how much the voice goes up and down (semitones, standard deviation)
  loudness_db  average loudness (dB, relative)

Tired speech is usually slower, with more pauses, flatter and quieter.
We compare today with this astronaut's own normal voice, like the ring baseline.

Rules (same as the hidden fatigue check):
  - it never changes the readiness score
  - it only sends a quiet note to Mission Control for a person to review
  - no audio is stored, only the four numbers
"""
from statistics import mean, pstdev

from app.data import store

FEATURES = ("speech_rate", "pause_ratio", "pitch_var", "loudness_db")
MIN_OWN = 3  # own check-ins needed before we trust the personal voice normal

# Starter normal used until the astronaut has 3 check-ins of their own (simulated, labelled)
STARTER = {"speech_rate": 150.0, "pause_ratio": 0.25, "pitch_var": 2.5, "loudness_db": -24.0}

# A cue counts when today's value moves this far from the personal normal, in the tired direction
LIMITS = {
    "speech_rate": ("lower", 0.15, "Slower speech than usual"),     # 15% slower
    "pause_ratio": ("higher", 0.10, "More pauses than usual"),      # +0.10 more silence
    "pitch_var": ("lower", 0.25, "Flatter voice than usual"),       # 25% less up and down
    "loudness_db": ("lower", 4.0, "Quieter than usual"),            # 4 dB quieter
}


def _history(crew: str) -> list[dict]:
    return store.load("voice_log", {}).get(crew, [])


def normal(crew: str) -> dict:
    """Personal voice normal: mean of the astronaut's first check-ins, or the starter values."""
    own = _history(crew)[:7]
    if len(own) < MIN_OWN:
        return {"source": "starter (simulated)", "count": len(own), "values": dict(STARTER)}
    vals = {k: round(mean(s[k] for s in own), 3) for k in FEATURES}
    spread = {k: round(pstdev(s[k] for s in own), 3) for k in FEATURES}
    return {"source": "your own voice", "count": len(own), "values": vals, "spread": spread}


def _valid(f: dict) -> bool:
    return all(isinstance(f.get(k), (int, float)) for k in FEATURES) and f["speech_rate"] > 0


def check(features: dict, base: dict) -> dict:
    """Compare today's voice with the normal. Returns cues in plain words; flag needs 2 or more."""
    b = base["values"]
    cues = []
    for k, (direction, limit, text) in LIMITS.items():
        if k == "loudness_db" and "spread" not in base:
            continue  # loudness depends on the microphone, so only compare with the person's own voice
        now, ref = features[k], b[k]
        if k in ("speech_rate", "pitch_var"):  # relative change
            change = (ref - now) / ref if ref else 0
        else:  # absolute change
            change = (now - ref) if direction == "higher" else (ref - now)
        if change >= limit:
            cues.append(text)
    return {"flag": len(cues) >= 2, "cues": cues}


def analyse(crew: str, features: dict) -> dict:
    """Check today's voice against the personal normal, then save the numbers (no audio)."""
    if not _valid(features):
        return {"ok": False, "message": "Voice too short to check. Try speaking for a few seconds."}
    f = {k: round(float(features[k]), 3) for k in FEATURES}
    base = normal(crew)
    result = check(f, base)
    log = store.load("voice_log", {})
    log.setdefault(crew, []).append(f)
    store.save("voice_log", log)
    return {"ok": True, "today": f, "normal": base, **result,
            "label": "Experimental · voice tone only · never changes the score"}
