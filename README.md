# shanghai-menu-watch

Daily menu watch for Shanghai Disney Resort (Shanghai Disneyland, Disneytown, the resort hotels), from Disney's official site shanghaidisneyresort.com. Separate from `disney-menu-watch` (Disneyland), `wdw-menu-watch` (Walt Disney World) and `tokyo-menu-watch`.

**Why this one is different.** Shanghai publishes each restaurant's menu as a designed PDF on `static.shanghaidisneyresort.com`, re-uploaded under a new filename (date suffix, e.g. `barbossas_bounty0901.pdf`) when it changes. The PDFs are real text with RMB prices, but the layout is columns and artwork, so item names cannot be paired to prices reliably by machine. The watcher therefore works at two levels:

- **Reliable — the alert.** Per venue: new PDF filename, changed PDF bytes, changed set of prices (with the exact numbers added and removed), added/removed English text lines, page-count change, venue added or removed, PDF removed from the page. Every changed PDF is rendered to JPEG page images committed under `data/renders/<slug>/` and linked from the issue comment, so the new menu can be read straight from GitHub.
- **Best-effort — the log.** `data/prices.csv` lists every price token with a guessed English item name (columns: Pulled, Venue, Location, PdfFile, Page, PriceRMB, ItemGuess, Slug). Prices are exact; names are heuristic. The rendered pages are the source of truth.

**How it runs.** Every 3 hours from 9am Shanghai time: sitemap → each `/en/experience/restaurant/<slug>` page (name, land, price range, PDF links) → download and parse each PDF → diff against `data/venues.csv` and `data/text/*.txt` → commit → one summary per day on the `daily-log` issue, plus an immediate comment when anything changed.

**Files.** `data/venues.csv` (one row per venue-PDF: Pulled, Slug, Venue, Location, PriceRange, PdfUrl, PdfFile, Sha, Bytes, Pages, PriceCount, Prices, LastChanged), `data/prices.csv`, `data/text/` (extracted text per PDF, used for the line diff), `data/renders/` (page images of changed menus), `data/last-daily.txt`.

**Coverage as of 2026-09-04.** 48 venues on the site, 28 with a menu PDF (30 PDFs). Third-party Disneytown tenants (Cheesecake Factory, IPPUDO, blue frog, etc.) have no PDF and are tracked for presence only. Two PDFs are image-only (Chip & Dale's Treehouse Treats, the Fantasyland hand-bun cart) — those still trigger on filename/byte changes and get rendered, just with no price tokens. Prices include Chinese VAT.

**Tuning.** `RENDER_DPI` (default 70) and `MAX_RENDER_PAGES` (default 8) env vars control render size. Renders are only written when a PDF changes, so the repo grows slowly.
