# -*- coding: utf-8 -*-
"""מודל נתונים אחיד למכרז — כולל שדות מפורטים למייל ולשמירה."""
from dataclasses import dataclass, field, asdict


@dataclass
class Tender:
    uid: str            # מזהה יציב לזיהוי כפילויות
    source: str         # שם המקור להצגה
    title: str
    url: str

    publisher: str = ""     # שם המפרסם (רמ"י / מועצה)
    ttype: str = ""         # סוג: פומבי / כוונה להתקשרות / פטור
    number: str = ""        # מספר מכרז / הליך

    # תאריכים
    open_date: str = ""     # תאריך פרסום / פתיחה
    close_date: str = ""    # מועד אחרון להגשה / סגירה

    # מיקום
    location: str = ""      # יישוב
    area: str = ""          # שטח העסקה (מ"ר)
    parcel: str = ""        # גוש / חלקה

    terms: str = ""         # מהות ההתקשרות / תיאור / תנאים

    # יצירת קשר
    contact_name: str = ""
    contact_email: str = ""
    contact_phone: str = ""

    bucket: str = ""        # wheat / grazing / both / general
    first_seen: str = ""    # תאריך גילוי ראשון (ISO) — נקבע בעת השמירה

    extra_text: str = field(default="", repr=False)

    def to_dict(self):
        d = asdict(self)
        d.pop("extra_text", None)
        return d

    @staticmethod
    def from_dict(d):
        fields = {k: v for k, v in d.items()
                  if k in Tender.__dataclass_fields__ and k != "extra_text"}
        return Tender(**fields)
