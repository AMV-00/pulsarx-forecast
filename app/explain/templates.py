"""Task 3: one reason sentence + expected effect for each change.

Numbers come only from the transparent model (`facts`) or the rules
(`change`). Claude may rephrase, but the result is rejected if it
contains any number that was not already in the template sentence.
"""
FACTOR_NAMES = {
    "en": {"sleep": "short sleep", "circadian": "a disrupted sleep cycle", "workload": "a heavy workload",
           "wake": "a long time awake", "cognitive": "lower focus"},
    "ar": {"sleep": "قلة النوم", "circadian": "اضطراب دورة النوم", "workload": "ضغط العمل",
           "wake": "طول مدة الاستيقاظ", "cognitive": "انخفاض التركيز"},
}
APPROVERS_AR = {"ground": "فريق الأرض", "commander": "قائد الطاقم (مؤقتًا لحين تأكيد الأرض)"}
LEVELS = {"en": {"low": "low", "medium": "medium", "high": "high"},
          "ar": {"low": "منخفض", "medium": "متوسط", "high": "مرتفع"}}

T = {
    "en": {
        "reason": "Fatigue risk is {level} mainly because of {factor}",
        "sleep": " ({sleep_hours} hours of sleep)",
        "longer_rest": "Extend {task} by {extra_minutes} minutes. {reason}. Expected effect: more recovery time before the next task.",
        "reorder": "Move {task} from {from} to {to}, after the rest. {reason}. Expected effect: the heavy task is done after recovery, not while tired.",
        "postpone": "Postpone {task} to the next day. {reason}. Expected effect: lower workload today.",
        "reassign": "Give {task} to crew member {to_crew} (has free time). {reason}. Expected effect: the task still gets done today with less fatigue risk.",
        "approval": " Needs approval by: {approver}.",
        "model_effect": " Model estimate: risk {before} → {after}.",
    },
    "ar": {
        "reason": "خطر الإرهاق {level} بسبب {factor}",
        "sleep": " ({sleep_hours} ساعات نوم)",
        "longer_rest": "تمديد {task} {extra_minutes} دقيقة. {reason}. الأثر المتوقع: وقت تعافٍ أكثر قبل المهمة التالية.",
        "reorder": "نقل {task} من {from} إلى {to} بعد الراحة. {reason}. الأثر المتوقع: تنفيذ المهمة الثقيلة بعد التعافي وليس وقت التعب.",
        "postpone": "تأجيل {task} لليوم التالي. {reason}. الأثر المتوقع: تخفيف ضغط العمل اليوم.",
        "reassign": "إعطاء {task} للرائد {to_crew} (عنده وقت فاضي). {reason}. الأثر المتوقع: تنجز المهمة اليوم بخطر إرهاق أقل.",
        "approval": " يحتاج موافقة: {approver}.",
        "model_effect": " تقدير النموذج: الخطر {before} ← {after}.",
    },
}


def reason_sentence(change: dict, facts: dict, lang: str = "en") -> str:
    """facts example: {"level": "high", "top_factor": "sleep", "sleep_hours": 5,
    optional "risk_before": 0.72, "risk_after": 0.55} -- all from the model."""
    t = T[lang]
    reason = t["reason"].format(level=LEVELS[lang][facts["level"]],
                                factor=FACTOR_NAMES[lang][facts.get("top_factor", "workload")])
    if facts.get("sleep_hours") is not None and facts.get("top_factor") == "sleep":
        reason += t["sleep"].format(sleep_hours=_fmt(facts["sleep_hours"]))
    text = t[change["type"]].format(reason=reason, **change)
    if facts.get("risk_before") is not None and facts.get("risk_after") is not None:
        text += t["model_effect"].format(before=_fmt(facts["risk_before"]), after=_fmt(facts["risk_after"]))
    approver = change["approver"]
    if lang == "ar":
        approver = APPROVERS_AR.get(approver.split(" ")[0], approver)
    return text + t["approval"].format(approver=approver)


def _fmt(x) -> str:
    return str(int(x)) if float(x).is_integer() else f"{x:g}"


def polish(sentence: str, client=None, lang: str = "en", model: str = "claude-sonnet-5-5") -> str:
    """Ask Claude for a smoother sentence. Falls back to the template if
    Claude adds/changes any number, or if there is no internet."""
    from app.explain.numbers import numbers_ok
    try:
        if client is None:
            from anthropic import Anthropic
            from dotenv import load_dotenv
            load_dotenv()
            client = Anthropic()
        language = "Arabic" if lang == "ar" else "English"
        msg = client.messages.create(
            model=model, max_tokens=200,
            system=("Rewrite the sentence to sound clear and calm for a mission team, in "
                    f"{language}. Keep the same meaning. Do not add, remove or change any number. "
                    "Return only the sentence."),
            messages=[{"role": "user", "content": sentence}],
        )
        out = "".join(b.text for b in msg.content if getattr(b, "type", "text") == "text").strip()
    except Exception:
        return sentence
    return out if out and numbers_ok(out, sentence) else sentence
