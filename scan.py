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
import hashlib, html, io, json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.request import Request, urlopen

import pdfplumber

HOST = 'https://www.shanghaidisneyresort.com'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36'
REPO = os.environ.get('GITHUB_REPOSITORY', 'scoopdisney/shanghai-menu-watch')
RAW = f'https://raw.githubusercontent.com/{REPO}/main/'
NOW_DT = datetime.now(timezone.utc)
TODAY = NOW_DT.strftime('%Y-%m-%d')
NOW = NOW_DT.strftime('%Y-%m-%d %H:%M')
RENDER_DPI = int(os.environ.get('RENDER_DPI', '70'))
MAX_RENDER_PAGES = int(os.environ.get('MAX_RENDER_PAGES', '8'))
