# SEO Audit CLI v3.1

🔍 Comprehensive website SEO auditor. One command, 12 checks, full report.

## Features

- **12 SEO Check Modules**: Meta tags, links, performance, security, mobile, structured data, accessibility, robots.txt, redirects, keyword density, Open Graph
- **Batch Scanning**: Audit multiple URLs from file
- **Multiple Exports**: JSON, CSV, JSONL, Markdown, HTML, summary text
- **Telegram Integration**: Send reports directly to Telegram
- **Competitor Comparison**: Compare multiple sites side-by-side
- **Scheduled Auditing**: Docker Compose with cron-like scheduling

## Install

```bash
pip install -e ".[reports,dev]"
# or
pip install requests
```

## Usage

```bash
# Single URL audit
python seo_audit.py example.com
python seo_audit.py https://mysite.com -v        # verbose
python seo_audit.py https://mysite.com --json     # JSON output

# Batch audit
python seo_audit.py --batch urls.txt --json --output results.json

# Compare sites
python seo_audit.py --compare site1.com site2.com site3.com
```

## Check Modules (11)

| # | Module | What It Checks | Impact |
|---|--------|---------------|--------|
| 1 | **Meta** | Title, description, canonical, charset | 🔴 High |
| 2 | **Links** | Internal/external, broken, nofollow | 🔴 High |
| 3 | **Performance** | Load time, page size, Core Web Vitals | 🔴 High |
| 4 | **Security** | HTTPS, HSTS, CSP, X-Frame-Options | 🔴 High |
| 5 | **Mobile** | Viewport, font size, tap targets | 🟡 Medium |
| 6 | **Structured Data** | JSON-LD, Microdata, Schema.org | 🟡 Medium |
| 7 | **Accessibility** | ARIA, skip links, alt text, landmarks | 🟡 Medium |
| 8 | **Robots.txt** | Directives, sitemaps, crawl-delay, blocks | 🔴 High |
| 9 | **Redirects** | Chain length, 301/302, loops, mixed protocol | 🔴 High |
| 10 | **Keywords** | Density, n-grams, stuffing, title alignment | 🟡 Medium |
| 11 | **Open Graph** | OG tags, Twitter Cards, image validation | 🟡 Medium |
| 12 | **Keyword Gap** | Keyword diversity, competitor gaps, content coverage | 🟡 Medium |

## Export Formats

```bash
# JSON
python seo_audit.py example.com --json

# CSV (batch)
python seo_audit.py --batch urls.txt --format csv --output results.csv

# Summary text
python seo_audit.py --batch urls.txt --format summary
```

## Docker

```bash
# Build
docker build -t seo-audit-cli .

# Run
docker run --rm seo-audit-cli example.com

# Scheduled auditing
docker compose up -d seo-audit-scheduled

# Run tests
docker compose run --rm test
```

## Telegram

```bash
export TELEGRAM_BOT_TOKEN=your_token
export TELEGRAM_CHAT_ID=your_chat_id
python seo_audit.py example.com --telegram
```

## Development

```bash
make install    # Install deps
make test       # Run tests
make lint       # Lint code
make test-cov   # Coverage report
```

## Tests

```bash
python -m pytest tests/ -v --tb=short
```

## License

MIT
