"""Snapshot comparison for shanghai-menu-watch: per-venue PDF change detection, rows, events."""
import os
from collections import Counter

from menu_pdf import is_latin
from shdr_report import describe_change
from shdr_util import read_csv

VEN_HEADER = ['Pulled', 'Slug', 'Venue', 'Location', 'PriceRange', 'PdfUrl', 'PdfFile', 'Sha', 'Bytes', 'Pages', 'PriceCount', 'Prices', 'LastChanged']
PR_HEADER = ['Pulled', 'Venue', 'Location', 'PdfFile', 'Page', 'PriceRMB', 'ItemGuess', 'Slug']


def compare(venues, pdf_results, TODAY, RAW):
    """Returns (venue_rows, price_rows, events, first_run)."""
    prev = {(r['Slug'], r['PdfUrl']): r for r in read_csv('data/venues.csv')}
    prev_by_slug = {}
    for (slug, url), r in prev.items():
        prev_by_slug.setdefault(slug, []).append(r)

    def text_path(slug, url):
        return f'data/text/{slug}__{os.path.basename(url)}.txt'

    venue_rows, price_rows = [], []
    events = []

    def fmt_prices(ps):
        return ' '.join(f'{p:g}' for p in ps)

    seen_slugs = set()
    for v in venues:
        seen_slugs.add(v['slug'])
        prev_urls = {r['PdfUrl'] for r in prev_by_slug.get(v['slug'], [])}
        if not v['pdfs']:
            venue_rows.append({'Pulled': TODAY, 'Slug': v['slug'], 'Venue': v['name'], 'Location': v['location'], 'PriceRange': v['price_range'], 'PdfUrl': '', 'PdfFile': '', 'Sha': '', 'Bytes': '', 'Pages': '', 'PriceCount': '', 'Prices': '', 'LastChanged': ''})
            if prev_urls - {''}:
                events.append(f'- **{v["name"]}** — menu PDF removed from its page (was {", ".join(os.path.basename(u) for u in prev_urls if u)})')
            continue
        for u in v['pdfs']:
            r = pdf_results.get((v['slug'], u))
            if not r:
                old = prev.get((v['slug'], u))
                if old:
                    venue_rows.append(old)
                continue
            prices_sorted = sorted(p[1] for p in r['prices'])
            old = prev.get((v['slug'], u))
            changed, why = False, []
            if old is None:
                if prev_by_slug.get(v['slug']):
                    changed = True
                    why.append(f'NEW PDF FILE `{os.path.basename(u)}` (was {", ".join(os.path.basename(x["PdfUrl"]) for x in prev_by_slug[v["slug"]] if x["PdfUrl"])})')
                elif prev:
                    events.append(f'- **{v["name"]}** — new venue on the site ({v["location"]}), menu `{os.path.basename(u)}`, {len(prices_sorted)} prices')
            else:
                if old['Sha'] != r['sha']:
                    changed = True
                    why.append('PDF bytes changed (same filename)')
                old_prices = sorted(float(x) for x in old['Prices'].split() if x)
                if old_prices != prices_sorted:
                    changed = True
                    gone = sorted((Counter(old_prices) - Counter(prices_sorted)).elements())
                    new = sorted((Counter(prices_sorted) - Counter(old_prices)).elements())
                    why.append(f'prices: {len(old_prices)} → {len(prices_sorted)}' + (f'; removed {fmt_prices(gone)}' if gone else '') + (f'; added {fmt_prices(new)}' if new else ''))
                if str(old['Pages']) != str(r['pages']):
                    why.append(f'pages {old["Pages"]} → {r["pages"]}')
            if changed:
                describe_change(v, u, r, old, prev_by_slug, why, TODAY, RAW, events, text_path, is_latin)
            last_changed = TODAY if (changed or old is None) else old['LastChanged']
            venue_rows.append({'Pulled': TODAY, 'Slug': v['slug'], 'Venue': v['name'], 'Location': v['location'], 'PriceRange': v['price_range'], 'PdfUrl': u, 'PdfFile': os.path.basename(u), 'Sha': r['sha'], 'Bytes': r['bytes'], 'Pages': r['pages'], 'PriceCount': len(prices_sorted), 'Prices': fmt_prices(prices_sorted), 'LastChanged': last_changed})
            with open(text_path(v['slug'], u), 'w', encoding='utf-8') as f:
                f.write('\n'.join(r['lines']) + '\n')
            for pg, val, name in r['prices']:
                price_rows.append({'Pulled': TODAY, 'Venue': v['name'], 'Location': v['location'], 'PdfFile': os.path.basename(u), 'Page': pg, 'PriceRMB': f'{val:g}', 'ItemGuess': name, 'Slug': v['slug']})
        for r0 in prev_by_slug.get(v['slug'], []):
            if r0['PdfUrl'] and r0['PdfUrl'] not in v['pdfs']:
                tp = text_path(v['slug'], r0['PdfUrl'])
                if os.path.exists(tp):
                    os.remove(tp)

    for slug in set(prev_by_slug) - seen_slugs:
        r0 = prev_by_slug[slug][0]
        events.append(f'- **{r0["Venue"]}** — venue no longer in Disney\'s sitemap')

    return venue_rows, price_rows, events, not prev
