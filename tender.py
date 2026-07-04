# -*- coding: utf-8 -*-
"""מודל נתונים אחיד למכרז."""
from dataclasses import dataclass, field


@dataclass
class Tender:
    uid: str            # מזהה יציב לזיהוי כפילויות (מקור + מספר)
    source: str         # שם המקור להצגה (למשל "מ.א. הגלבוע" / "רמ״י")
    title: str
    url: str
    publisher: str = ""    # שם המפרסם (רלוונטי ל-mr.gov.il)
    ttype: str = ""        # סוג: פומבי / כוונה להתקשרות / פטור
    open_date: str = ""
    close_date: str = ""
    location: str = ""     # יישוב/אזור שחולץ מדף הפרט
    bucket: str = ""       # wheat / grazing / general — מתמלא בסיווג

    # טקסט חופשי נוסף שנאסף לצורך סינון (לא מוצג)
    extra_text: str = field(default="", repr=False)
