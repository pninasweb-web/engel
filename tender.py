# -*- coding: utf-8 -*-
"""מודל נתונים אחיד למכרז — כולל שדות מפורטים למייל."""
from dataclasses import dataclass, field


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

    # תוכן
    terms: str = ""         # מהות ההתקשרות / תיאור / תנאים

    # יצירת קשר
    contact_name: str = ""
    contact_email: str = ""
    contact_phone: str = ""

    bucket: str = ""        # wheat / grazing / both / general
    extra_text: str = field(default="", repr=False)
