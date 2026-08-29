# Witch Cult Translations Scraper
A Python script that scrapes the [Witch Cult Translations](https://witchculttranslation.com/table-of-content/) table of contents (Re:Zero WN fan translation), groups chapter links by sotry arc, and saves each arc's chapters into a single readable '.txt' file

## What it does

- Parses the site's Table of Contents page to build a list of arcs and their chapters
- Visits each chapter link and extracts the readable text, handling a few different sitr layouts(chapters are hosted across multiple domains)
- Skips links it can't cleanly extract text from(PDFs, Mega.nz files) and logs why, rather then failing silently
- Writes one '.txt' file per arc into an 'Arcs/' foldeer, wih each chapter cleanly separated

## Requirements

- Python 3.10+ (Uses the 'Str | None' type hint syntax)
- 'requests'
- 'beautifulsoup4'

install dependencies:

'''bash
pip install requests beautifulsoup4
'''

## Usage

Preview the arc/chapter plan without fetching any chapter pages:

'''bash
python wct_scraper.py --list
'''

Scrape everything:

'''bash
python wct_scraper.py
'''

Scape only specific arcs:

'''bash
python wct_scraper.py --arc 1 3
'''

Output is saved to 'Arcs/Arc 01, one file per arc.

## Notes

- The script waits 1.5 seconds between chapter requests to avoid hammering the source servers.  
- Site structures can change over time - if '--list' shows 0 arcs or 0 chapters, the page's HTML likely no longer matches the  selectors this script expects.
- This is for personal, offline reading conveniences of a freely available fan translation. Respect the translators' work and the source of site's term.

## License

Apache License 2.0.