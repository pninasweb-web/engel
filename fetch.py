# -*- coding: utf-8 -*-
"""עוזר HTTP קטן — session עם User-Agent, timeout ו-retry בסיסי."""
import time
import requests

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    ),
    "Accept-Language": "he-IL,he;q=0.9",
}

_session = requests.Session()
_session.headers.update(_HEADERS)


def get_html(url, tries=3, timeout=30):
    """מחזיר את גוף ה-HTML כטקסט, או None אם נכשל אחרי כמה ניסיונות."""
    last = None
    for attempt in range(tries):
        try:
            resp = _session.get(url, timeout=timeout)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.5 * (attempt + 1))
    print(f"  ! fetch failed: {url} ({last})")
    return None
