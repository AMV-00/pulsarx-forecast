"""Task 4: saved answers NOVA uses when there is no internet or the API fails.

No numbers are invented here: messages only repeat values passed in.
"""
ANSWERS = {
    "en": {
        "greeting": "Good morning. I'm NOVA. I have four quick questions about how you feel today.",
        "offline_notice": "I'm working offline right now, so my answers are shorter, but your check-in is saved.",
        "thanks": "Thank you. Your check-in is complete and has been sent for review.",
        "risk_low": "Your fatigue risk looks low today. No schedule changes are suggested.",
        "risk_medium": "Your fatigue risk looks medium today. I've suggested small schedule changes for the ground team to review.",
        "risk_high": "Your fatigue risk looks high today. I've suggested schedule changes to protect your rest. The ground team will review them.",
        "mars_mode": "Ground reply will take a while. A temporary change is ready for the commander to approve until ground confirms.",
        "hedging": "Thanks. If you feel more tired than usual, it's okay to say so. It helps plan your day, it doesn't cancel your mission.",
        "unknown": "Sorry, I didn't catch that. Could you say it another way?",
    },
    "ar": {
        "greeting": "صباح الخير، أنا NOVA. عندي أربعة أسئلة سريعة عن حالتك اليوم.",
        "offline_notice": "أنا الحين بدون إنترنت، فإجاباتي أقصر، بس إجاباتك محفوظة.",
        "thanks": "شكرًا لك. خلص التسجيل اليومي وانرسل للمراجعة.",
        "risk_low": "خطر الإرهاق عندك اليوم منخفض. ما فيه تعديلات مقترحة على الجدول.",
        "risk_medium": "خطر الإرهاق عندك اليوم متوسط. اقترحت تعديلات بسيطة يراجعها فريق الأرض.",
        "risk_high": "خطر الإرهاق عندك اليوم مرتفع. اقترحت تعديلات تحمي وقت راحتك، ويراجعها فريق الأرض.",
        "mars_mode": "رد الأرض بيتأخر. فيه تعديل مؤقت جاهز يعتمده قائد الطاقم لحين تأكيد الأرض.",
        "hedging": "شكرًا. لو تحس بتعب أكثر من العادة، عادي تقوله. هذا يساعدنا نرتب يومك، وما يلغي مهمتك.",
        "unknown": "آسفة، ما فهمت. ممكن تقولها بطريقة ثانية؟",
    },
}


def answer(key: str, lang: str = "en") -> str:
    return ANSWERS.get(lang, ANSWERS["en"]).get(key, ANSWERS[lang]["unknown"])
