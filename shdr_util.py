"""HTTP + CSV helpers for shanghai-menu-watch."""
import csv, html, os, re, time
from urllib.request import Request, urlopen

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36'


def get(url, timeout=90, binary=False):
    last = None
    for attempt in range(1, 4):
        try:
            req = Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'})
            with urlopen(req, timeout=timeout) as r:
                data = r.read()
            return data if binary else data.decode('utf-8', 'ignore')
        except Exception as e:  # noqa
            last = e
            time.sleep(1.5 * attempt)
    raise last


def strip_html(h):
    t = re.sub(r'<script.*?</script>', ' ', h, flags=re.S)
    t = re.sub(r'<style.*?</style>', ' ', t, flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)
    return html.unescape(re.sub(r'\s+', ' ', t)).strip()


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, header):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in header})
