# -*- coding: utf-8 -*-
"""
מסד הנתונים של המכרזים — נשמר בקובץ data.json ומאפשר לזכור:
  - כל מכרז רלוונטי שנמצא אי-פעם (עם תאריך גילוי ראשון) → לסעיף "השבוע" ולספרדשיט
  - אילו מזהי mr.gov.il כבר נבדקו → כדי לא למשוך שוב דפי פרט מיותרים
ב-GitHub Actions הקובץ נשמר בחזרה ל-repo כדי לזכור בין הרצות.
"""
import json
import os
from datetime import date, datetime, timedelta

DB_FILE = os.path.join(os.path.dirname(__file__), "data.json")


def load_db():
    """מחזיר (tenders: dict uid->record, mr_evaluated: set)."""
    if not os.path.exists(DB_FILE):
        return {}, set()
    try:
        with open(DB_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("tenders", {}), set(data.get("mr_evaluated", []))
    except Exception:  # noqa: BLE001
        return {}, set()


def save_db(tenders, mr_evaluated):
    payload = {
        "tenders": tenders,
        "mr_evaluated": sorted(mr_evaluated),
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)


def today_iso():
    return date.today().isoformat()


def within_days(iso_str, days):
    """האם התאריך (ISO) נמצא בטווח של N הימים האחרונים."""
    if not iso_str:
        return False
    try:
        d = date.fromisoformat(iso_str[:10])
    except ValueError:
        return False
    return d >= date.today() - timedelta(days=days)
