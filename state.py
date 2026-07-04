# -*- coding: utf-8 -*-
"""
זיכרון המכרזים שכבר טופלו — נשמר בקובץ seen.json.
ב-GitHub Actions הקובץ נשמר בחזרה ל-repo כדי לזכור בין הרצות.
"""
import json
import os

STATE_FILE = os.path.join(os.path.dirname(__file__), "seen.json")


def load():
    if not os.path.exists(STATE_FILE):
        return set()
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("seen", []))
    except Exception:  # noqa: BLE001
        return set()


def save(seen):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"seen": sorted(seen)}, f, ensure_ascii=False, indent=0)
