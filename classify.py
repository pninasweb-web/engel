# -*- coding: utf-8 -*-
"""סיווג מכרז לקבוצה (חיטה / מרעה / כללי) ובדיקת רלוונטיות גאוגרפית.

חשוב: ההתאמה היא ברמת *מילה שלמה* (עם אותיות שימוש ב/ה/ל/מ/ו/כ/ש בהתחלה),
ולא תת-מחרוזת — אחרת "נין" (יישוב בגלבוע) היה מזוהה בטעות בתוך "סחנין".
"""
import re
from config import (
    WHEAT_KEYWORDS, GRAZING_KEYWORDS, GENERAL_AGRI_KEYWORDS,
    REGION_SETTLEMENTS,
)

_HEB_PREFIX = "בהלמוכש"          # אותיות שימוש שעשויות להיצמד למילה
_HEB = "א-ת"


def _word_match(text, term):
    """התאמת מילה שלמה. ביטויים עם רווח/גרש מותאמים כתת-מחרוזת (בטוח דיו)."""
    if " " in term or "'" in term or '"' in term or "׳" in term or "״" in term:
        return term in text
    pattern = (
        rf"(?:^|[^{_HEB}])[{_HEB_PREFIX}]{{0,2}}"
        + re.escape(term)
        + rf"(?![{_HEB}])"
    )
    return re.search(pattern, text) is not None


def _has_any(text, keywords):
    return any(_word_match(text, kw) for kw in keywords)


def bucket(text):
    """מחזיר 'wheat' / 'grazing' / 'both' / 'general' — או None אם לא חקלאי."""
    wheat = _has_any(text, WHEAT_KEYWORDS)
    grazing = _has_any(text, GRAZING_KEYWORDS)
    if wheat and grazing:
        return "both"
    if wheat:
        return "wheat"
    if grazing:
        return "grazing"
    if _has_any(text, GENERAL_AGRI_KEYWORDS):
        return "general"
    return None


def in_region(text):
    """האם הטקסט מזכיר יישוב/אזור ברדיוס הרלוונטי (התאמת מילה שלמה)."""
    return _has_any(text, REGION_SETTLEMENTS)


def expand_bucket(bucket):
    """'both' = חיטה וגם מרעה."""
    return ["wheat", "grazing"] if bucket == "both" else [bucket]


def is_visible(bucket, email_buckets):
    """האם הקבוצה נכללת בתצוגה לפי ההגדרה (EMAIL_BUCKETS)."""
    return bool(set(expand_bucket(bucket)) & set(email_buckets))
