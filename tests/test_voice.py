from app import voice
from app.data import store

NORMAL = {"speech_rate": 150, "pause_ratio": 0.25, "pitch_var": 2.5, "loudness_db": -24}


def test_normal_voice_is_not_flagged():
    r = voice.check(NORMAL, {"values": voice.STARTER})
    assert r["flag"] is False and r["cues"] == []


def test_tired_voice_is_flagged_with_plain_cues():
    tired = {"speech_rate": 110, "pause_ratio": 0.45, "pitch_var": 1.4, "loudness_db": -30}
    r = voice.check(tired, {"values": voice.STARTER})
    assert r["flag"] is True
    assert "Slower speech than usual" in r["cues"] and "Flatter voice than usual" in r["cues"]


def test_one_cue_alone_does_not_flag():
    r = voice.check({**NORMAL, "speech_rate": 100}, {"values": voice.STARTER})
    assert r["cues"] == ["Slower speech than usual"] and r["flag"] is False


def test_personal_normal_after_three_checkins(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    slow = {"speech_rate": 120, "pause_ratio": 0.3, "pitch_var": 2.0, "loudness_db": -26}
    for _ in range(3):
        voice.analyse("Z", slow)
    base = voice.normal("Z")
    assert base["source"] == "your own voice" and base["values"]["speech_rate"] == 120
    # the same slow voice is normal for this person, so no flag
    assert voice.analyse("Z", slow)["flag"] is False


def test_too_short_voice_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    assert voice.analyse("Z", {"speech_rate": 0})["ok"] is False
