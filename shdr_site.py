"""Site + PDF gathering for shanghai-menu-watch: sitemap discovery, venue pages, PDF download/parse."""
import hashlib, os, re, sys
from concurrent.futures import ThreadPoolExecutor

from menu_pdf import parse_pdf
from shdr_util import get, strip_html

HOST = 'https://www.shanghaidisneyresort.com'


def gather(NOW):
    """Returns dict(venues, gone_404, failures, pdf_results). Calls abort() (exit 0) on structural failures."""
    def abort(reason):
        os.makedirs('data', exist_ok=True)
        with open('summary.md', 'w', encoding='utf-8') as f:
            f.write(f'## Shanghai menu scan {NOW} UTC — ABORTED\n\n{reason}\n\nSnapshot left untouched.\n')
        open('POST_COMMENT', 'w').write('1')
        print('ABORTED:', reason)
        sys.exit(0)

    try:
        sm = get(HOST + '/sitemap.xml')
    except Exception as e:
        abort(f'Could not fetch {HOST}/sitemap.xml: {e}')
    slugs = sorted(set(re.findall(r'/experience/restaurant/([a-z0-9-]+)', sm)))
    if len(slugs) < 30:
        abort(f'Sitemap listed only {len(slugs)} restaurant slugs (expected ~50). Site structure may have changed.')

    def venue_info(slug):
        h = get(f'{HOST}/en/experience/restaurant/{slug}')
        t = strip_html(h)
        title = re.search(r'<title>([^<]*)</title>', h)
        name = (title.group(1).split('|')[0].strip() if title else slug)
        loc = re.search(r'Location:\s*(.+?)\s+Cuisine:', t)
        pr = re.search(r'Price Range:\s*(.+?)\s+Today', t)
        pdfs = sorted(set(u for u in re.findall(r'https://static\.shanghaidisneyresort\.com/[^"\'\\\s<>]+?\.pdf', h) if 'park-map' not in u))
        if 'Someone ate the page' in t and not pdfs:
            return None
        return {'slug': slug, 'name': name, 'location': loc.group(1).strip() if loc else '', 'price_range': pr.group(1).strip() if pr else '', 'pdfs': pdfs}

    failures = []
    venues = []
    gone_404 = []
    def _safe(slug):
        try:
            return venue_info(slug)
        except Exception as e:
            return {'slug': slug, 'error': str(e)}
    with ThreadPoolExecutor(4) as ex:
        for v in ex.map(_safe, slugs):
            if v is None:
                gone_404.append('')
                continue
            if 'error' in v:
                failures.append(f"{v['slug']}: {v['error']}")
            else:
                venues.append(v)
    if len(failures) > 8:
        abort(f'{len(failures)} venue pages failed:\n' + '\n'.join('- ' + f for f in failures))

    def fetch_pdf(url):
        data = get(url, timeout=180, binary=True)
        if not data.startswith(b'%PDF'):
            raise RuntimeError('not a PDF')
        sha = hashlib.sha256(data).hexdigest()[:16]
        pages, lines, prices = parse_pdf(data)
        return {'url': url, 'sha': sha, 'bytes': len(data), 'pages': pages, 'lines': lines, 'prices': prices, 'data': data}

    pdf_jobs = [(v, u) for v in venues for u in v['pdfs']]
    pdf_results = {}
    def _safe_pdf(job):
        v, u = job
        try:
            return (v['slug'], u, fetch_pdf(u))
        except Exception as e:
            return (v['slug'], u, {'error': str(e)})
    with ThreadPoolExecutor(4) as ex:
        for slug, u, r in ex.map(_safe_pdf, pdf_jobs):
            if 'error' in r:
                failures.append(f'{slug} {os.path.basename(u)}: {r["error"]}')
            else:
                pdf_results[(slug, u)] = r

    if len(pdf_results) < max(10, len(pdf_jobs) - 6):
        abort(f'Only {len(pdf_results)} of {len(pdf_jobs)} menu PDFs downloaded.\n' + '\n'.join('- ' + f for f in failures))

    return {'venues': venues, 'gone_404': gone_404, 'failures': failures, 'pdf_results': pdf_results, 'abort': abort}
