# -*- coding: utf-8 -*-
"""
נקודת הכניסה.

מצבים:
    python3 main.py               הרצה יומית: מוצא מכרזים, מעדכן מסד, שולח מייל
                                   עם "חדשים" + "רלוונטיים השבוע" אם יש חדשים.
    python3 main.py --weekly      מייל סיכום שבועי (כל מה שנמצא ב-7 הימים האחרונים).
    python3 main.py --dry-run     כמו יומי אבל בלי לשלוח מייל ובלי לשמור מצב.
    python3 main.py --preview     מרנדר את המייל היומי לקובץ email_preview.html.

תמיד מתחדש קובץ הספרדשיט (tenders.xlsx) ממסד הנתונים.
"""
import sys

import config
import classify
import state
import notify
import spreadsheet
import sheets
from tender import Tender
from sources import councils, mr_gov

# תקרת דפי-פרט לחילוץ בהרצה אחת (הגנה מפני הצפה)
MAX_NEW_DETAIL = 250


# ---------------------------------------------------------------------------
# איסוף מכרזים חקלאיים (כל הקבוצות — הסינון לתצוגה קורה בהמשך)
# ---------------------------------------------------------------------------

def collect_from_councils():
    out = []
    for t in councils.scrape_all(config.COUNCILS):
        b = classify.bucket(f"{t.title} {t.terms}")
        if b:
            t.bucket = b
            councils.enrich_match(t)
            out.append(t)
    return out


def collect_from_mr_gov(mr_evaluated):
    out = []
    candidates = mr_gov.search_candidates()
    fresh = [t for t in candidates.values() if t.uid not in mr_evaluated]
    fresh.sort(key=lambda t: t.uid, reverse=True)
    capped = fresh[:MAX_NEW_DETAIL]
    if len(fresh) > MAX_NEW_DETAIL:
        print(f"  ⚠ {len(fresh)} מועמדים חדשים — מטפל ב-{MAX_NEW_DETAIL}, השאר בהרצה הבאה")

    for t in capped:
        mr_evaluated.add(t.uid)          # נבדק — לא נמשוך שוב את דף הפרט
        mr_gov.enrich_details(t)
        if not classify.in_region(f"{t.location} {t.title}"):
            continue
        t.bucket = classify.bucket(f"{t.title} {t.location}") or "general"
        out.append(t)
    return out


# ---------------------------------------------------------------------------
# עזרי תצוגה
# ---------------------------------------------------------------------------

def _fresh(t):
    """מכרז רלוונטי: מועד ההגשה לא עבר, ופורסם לא מזמן (MAX_AGE_DAYS)."""
    from datetime import date, timedelta
    import re
    def parse(s):
        m = re.match(r"(\d{2})/(\d{2})/(\d{4})", s or "")
        if not m:
            return None
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    today = date.today()
    close = parse(t.close_date)
    if close and close < today:            # מועד ההגשה עבר
        return False
    published = parse(t.open_date)
    if published and published < today - timedelta(days=config.MAX_AGE_DAYS):
        return False                        # ישן מדי — כנראה נסגר
    return True


def _visible(tenders):
    return [t for t in tenders
            if classify.is_visible(t.bucket, config.EMAIL_BUCKETS) and _fresh(t)]


def _week_records(db_tenders):
    """מכרזים שנמצאו ב-7 הימים האחרונים, לפי סדר יורד של תאריך גילוי."""
    recs = [Tender.from_dict(r) for r in db_tenders.values()
            if state.within_days(r.get("first_seen", ""), config.WEEK_DAYS)]
    recs = _visible(recs)
    recs.sort(key=lambda t: t.first_seen, reverse=True)
    return recs


# ---------------------------------------------------------------------------
# מצב יומי
# ---------------------------------------------------------------------------

def run_daily(dry_run=False, preview=False):
    db_tenders, mr_evaluated = state.load_db()
    print(f"מסד נתונים: {len(db_tenders)} מכרזים מוכרים")
    today = state.today_iso()

    print("סורק מועצות אזוריות…")
    current = collect_from_councils()
    print("סורק מינהל הרכש (רמ״י / משרד החקלאות)…")
    current += collect_from_mr_gov(mr_evaluated)

    # מיזוג למסד: חדשים מקבלים first_seen=today; קיימים שומרים על התאריך המקורי
    new_today = []
    for t in current:
        if t.uid in db_tenders:
            t.first_seen = db_tenders[t.uid].get("first_seen", today)
        else:
            t.first_seen = today
            new_today.append(t)
        db_tenders[t.uid] = t.to_dict()

    new_visible = _visible(new_today)
    week_visible = _week_records(db_tenders)
    new_uids = {t.uid for t in new_visible}
    week_older = [t for t in week_visible if t.uid not in new_uids]

    print(f"\nחדשים היום (מוצגים): {len(new_visible)} | רלוונטיים השבוע: {len(week_visible)}")
    for t in new_visible:
        print(f"  🆕 [{t.bucket}] {t.source} · {t.location or '—'} · {t.title[:60]}")

    if preview:
        with open("email_preview.html", "w", encoding="utf-8") as f:
            f.write(notify.build_daily(new_visible, week_older))
        spreadsheet.build(_visible([Tender.from_dict(r) for r in db_tenders.values()]))
        print("\nנשמרו: email_preview.html + tenders.xlsx (בלי שליחה/שמירת מצב)")
        return

    if dry_run:
        print("\n(dry-run: לא נשלח מייל ולא נשמר מצב)")
        return

    # בונים את הספרדשיט (לצירוף) ומעדכנים את הגיליון החי בגוגל
    all_visible = _visible([Tender.from_dict(r) for r in db_tenders.values()])
    spreadsheet.build(all_visible)
    sheets.push(all_visible)

    # מייל נשלח רק כשיש מכרזים חדשים
    if new_visible:
        notify.send_daily(new_visible, week_older)
    else:
        print("אין מכרזים חדשים היום — לא נשלח מייל.")

    state.save_db(db_tenders, mr_evaluated)
    print(f"מסד עודכן: {len(db_tenders)} מכרזים · הספרדשיט חודש.")


# ---------------------------------------------------------------------------
# מצב שבועי
# ---------------------------------------------------------------------------

def run_weekly():
    db_tenders, _ = state.load_db()
    week = _week_records(db_tenders)
    # מרעננים את הספרדשיט המצורף ואת הגיליון החי מכל הארכיון
    all_visible = _visible([Tender.from_dict(r) for r in db_tenders.values()])
    spreadsheet.build(all_visible)
    sheets.push(all_visible)
    print(f"סיכום שבועי: {len(week)} מכרזים רלוונטיים ב-7 הימים האחרונים")
    if week:
        notify.send_weekly(week)
    else:
        print("אין מכרזים רלוונטיים השבוע — לא נשלח סיכום.")


if __name__ == "__main__":
    if "--weekly" in sys.argv:
        run_weekly()
    else:
        run_daily(dry_run="--dry-run" in sys.argv, preview="--preview" in sys.argv)
