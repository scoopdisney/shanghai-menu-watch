"""PDF helpers for shanghai-menu-watch: text lines + price tokens with name guesses."""
import io, re

import pdfplumber

def detriple(s):
    return re.sub(r'(.)\1\1', r'\1', s)  # fake-bold overprint: "SSSaaalllttt" -> "Salt"

def is_latin(w):
    return re.search(r'[A-Za-z]', w) is not None and not re.search(r'[\u4e00-\u9fff]', w)

PRICE_RE = re.compile(r'(\d{1,4}(?:\.\d{1,2})?)(元)?$')

def parse_pdf(data):
    """Returns (pages, lines, prices[(page, value, name_guess)])."""
    lines, prices = [], []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        npages = len(pdf.pages)
        for pi, pg in enumerate(pdf.pages):
            try:
                words = pg.extract_words(use_text_flow=False)
            except Exception:
                words = []
            for w in words:
                w['text'] = detriple(w['text'])
            by_line = {}
            for w in words:
                by_line.setdefault(round(w['top'] / 4), []).append(w)
            for k in sorted(by_line):
                txt = ' '.join(x['text'] for x in sorted(by_line[k], key=lambda x: x['x0']))
                if txt.strip():
                    lines.append(f'p{pi+1}: {txt}')
            page_has_yuan = any(re.search(r'元|RMB|毫升|克/g|ml|人民币', w['text']) for w in words)
            for w in words:
                m = PRICE_RE.fullmatch(w['text'])
                if not m:
                    continue
                val = float(m.group(1))
                ok = bool(m.group(2)) or (page_has_yuan and val < 1900)
                if not ok:
                    for v in words:
                        if ('元' in v['text'] or 'RMB' in v['text']) and abs(v['x0'] - w['x0']) < 80 and -5 <= v['top'] - w['top'] <= 40:
                            ok = True
                            break
                if not ok or not (5 <= val <= 5000):
                    continue
                cands = [v for v in words if is_latin(v['text']) and w['top'] - 170 <= v['top'] <= w['top'] + 6
                         and v['x0'] < w['x1'] + 40 and v['x1'] > w['x0'] - 260
                         and v['text'] not in ('RMB', '/RMB', '/', 'g', 'ml')
                         and not re.match(r'^[\d/]+(克|毫升)?', v['text']) and not re.search(r'克/g|毫升/ml|^\(|^[A-Z]$', v['text'])]
                by = {}
                for v in cands:
                    by.setdefault(round(v['top'] / 4), []).append(v)
                name_lines = []
                for k in sorted(by, reverse=True):
                    txt = ' '.join(x['text'] for x in sorted(by[k], key=lambda x: x['x0']))
                    if len(txt) < 2:
                        continue
                    name_lines.insert(0, txt)
                    if len(name_lines) >= 3:
                        break
                prices.append((pi + 1, val, re.sub(r'\s+', ' ', ' '.join(name_lines)).strip()[:120]))
    return npages, lines, prices
