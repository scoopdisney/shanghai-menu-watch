#!/usr/bin/env python3
"""Shanghai Disney Resort menu watch — SEPARATE from the Disneyland, WDW and Tokyo trackers.

Shanghai publishes each restaurant's menu as a designed PDF on static.shanghaidisneyresort.com
(re-uploaded under a new filename when it changes, e.g. barbossas_bounty0901.pdf). Those PDFs are
real text, bilingual, RMB prices — but the layout is columns and art, so item names cannot be
paired with prices reliably by machine. So this watcher works at two levels:

  RELIABLE (the alert):  per venue — new PDF filename, changed PDF bytes, changed set of prices,
                         added/removed text lines, page-count change, venue added/removed, PDF
                         removed from the page. Changed PDFs are rendered to page images and
                         committed so the human can read the new menu straight from the issue.
  BEST-EFFORT (the log): data/prices.csv — every price token with a guessed English item name.
                         Names are heuristic; prices are exact.

Outputs: data/venues.csv, data/prices.csv, data/text/<slug>__<pdf>.txt, data/renders/<slug>/…,
         data/last-daily.txt, summary.md, POST_COMMENT
"""
import os
from datetime import datetime, timezone

from shdr_util import write_csv
from shdr_report import write_summary
from shdr_diff import compare, VEN_HEADER, PR_HEADER
from shdr_site import gather

REPO = os.environ.get('GITHUB_REPOSITORY', 'scoopdisney/shanghai-menu-watch')
RAW = f'https://raw.githubusercontent.com/{REPO}/main/'
NOW_DT = datetime.now(timezone.utc)
TODAY = NOW_DT.strftime('%Y-%m-%d')
NOW = NOW_DT.strftime('%Y-%m-%d %H:%M')

_g = gather(NOW)
venues, gone_404, failures, pdf_results = _g['venues'], _g['gone_404'], _g['failures'], _g['pdf_results']

os.makedirs('data/text', exist_ok=True)
os.makedirs('data/renders', exist_ok=True)

venue_rows, price_rows, events, first_run = compare(venues, pdf_results, TODAY, RAW)

write_csv('data/venues.csv', venue_rows, VEN_HEADER)
write_csv('data/prices.csv', price_rows, PR_HEADER)

write_summary({'NOW': NOW, 'TODAY': TODAY, 'venues': venues, 'failures': failures, 'events': events, 'venue_rows': venue_rows,
               'gone_404': len(gone_404), 'pdf_count': len(pdf_results), 'price_count': len(price_rows), 'first_run': first_run})
