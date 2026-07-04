# -*- coding: utf-8 -*-
"""
נקודת הכניסה. מריץ את כל המקורות, מסנן לפי נושא ואזור,
זוכר מה כבר נשלח, ושולח מייל רק על מכרזים חדשים.

הרצה מקומית לבדיקה (בלי לשלוח מייל ובלי לשמור מצב):
    python3 main.py --dry-run
"""
import sys

import config
import classify
import state
import notify
from sources import councils, mr_gov

# תקרת דפי-פרט לחילוץ בהרצה אחת (הגנה מפני הצפה). מספיק גבוה כדי
# שההרצה הראשונה תכסה את כל המכרזים הפעילים; בהרצות הבאות ממילא יש מעט חדשים.
MAX_NEW_DETAIL = 250


def collect_council_matches(seen, processed):
    """מכרזים מהמועצות — כבר באזור בהגדרה, צריך רק סינון נושאי."""
    matches = []
    for t in councils.scrape_all(config.COUNCILS):
        if t.uid in seen:
            continue
        processed.add(t.uid)
        b = classify.bucket(t.title)
        if b:
            t.bucket = b
            matches.append(t)
    return matches


def collect_mr_gov_matches(seen, processed):
    """מכרזי רמ"י/משרד החקלאות — צריך גם סינון נושאי וגם גאוגרפי."""
    matches = []
    candidates = mr_gov.search_candidates()
    new = [t for t in candidates.values() if t.uid not in seen]
    # החדשים קודם (מספר פרסום גבוה = חדש יותר), עם תקרה
    new.sort(key=lambda t: t.uid, reverse=True)
    capped = new[:MAX_NEW_DETAIL]
    if len(new) > MAX_NEW_DETAIL:
        print(f"  ⚠ {len(new)} מועמדים חדשים — מטפל ב-{MAX_NEW_DETAIL} הראשונים, השאר בהרצה הבאה")

    for t in capped:
        processed.add(t.uid)
        mr_gov.enrich_location(t)
        # סינון אזור לפי היישוב שחולץ + הכותרת (לא לפי טקסט הנכס הרחב,
        # כדי לא לתפוס יישובים רחוקים שנכללים באותה עסקה)
        if not classify.in_region(f"{t.location} {t.title}"):
            continue
        b = classify.bucket(f"{t.title} {t.location}") or "general"
        t.bucket = b
        matches.append(t)
    return matches


def main(dry_run=False):
    seen = state.load()
    print(f"זיכרון: {len(seen)} מכרזים מוכרים")
    processed = set()

    print("סורק מועצות אזוריות…")
    matches = collect_council_matches(seen, processed)
    print("סורק מינהל הרכש (רמ״י / משרד החקלאות)…")
    matches += collect_mr_gov_matches(seen, processed)

    print(f"\nנמצאו {len(matches)} מכרזים חדשים ורלוונטיים.")
    for t in matches:
        print(f"  [{t.bucket}] {t.source} · {t.location or '—'} · {t.title[:70]}")

    if dry_run:
        print("\n(dry-run: לא נשלח מייל ולא נשמר מצב)")
        return

    if matches:
        notify.send(matches)
    else:
        print("אין מכרזים חדשים — לא נשלח מייל.")

    # מוסיפים לזיכרון את כל מה שטופל (גם מה שלא התאים) כדי לא לבדוק שוב
    state.save(seen | processed)
    print(f"זיכרון עודכן: {len(seen | processed)} מכרזים.")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
