## [3.1.0] - 2026-03-03

### Added
- **Keyword Gap Analyzer** (`audit/checks/keyword_gap.py`): Competitor keyword gap analysis with keyword extraction, bigram analysis, diversity scoring, coverage metrics, and actionable recommendations for content strategy
- 11 comprehensive test cases for keyword gap functionality
- KeywordGapCheck integration into audit framework

### Changed
- Check modules: 11 → 12 (+keyword_gap)
- Total test count: 265 tests passing
# Changelog

## [3.0.0] - 2026-02-28

### Added
- **Robots.txt Analyzer** (`audit/checks/robots.py`): Deep robots.txt parsing with directive analysis, sitemap discovery and validation, crawl-delay detection, path blocking checks, and SEO-critical path alerts
- **Redirect Chain Analyzer** (`audit/checks/redirect.py`): Full redirect chain tracing, loop detection, mixed-protocol warnings, temporary vs permanent redirect analysis, canonical URL consistency checks
- **Keyword Density Analyzer** (`audit/checks/keyword.py`): Word frequency analysis, bigram/trigram extraction, lexical diversity scoring, keyword stuffing detection, title/meta keyword alignment
- **Open Graph & Twitter Card Validator** (`audit/checks/opengraph.py`): OG tag completeness, Twitter Card type validation, image URL checks, dimension recommendations, title consistency analysis
- **Batch Export Engine** (`audit/reports/export.py`): CSV, JSON, JSONL, and text summary export formats with file save support
- Docker Compose with scheduled auditing and test runner
- Dockerfile for containerized deployment
- Makefile with install/test/lint/format/clean/docker targets
- GitHub Actions CI: lint + test (Python 3.10/3.11/3.12) + Docker build
- Comprehensive test suites for all 4 new modules + export (100+ new tests)

### Fixed
- Mobile check: `requests` module-level import for proper test mocking
- Telegram report test: score calculation consistency (add_issue deduction)
- 13 previously failing tests now pass

### Changed
- Check modules: 7 → 11 (+robots, redirects, keywords, opengraph)
- Total test count: 178 → 280+
- Updated version to 3.0.0

## [2.0.0] - 2026-02-27

### Added
- 7 check modules (meta, links, performance, security, mobile, structured data, accessibility)
- Batch scanning with concurrent URL auditing
- Competitor comparison mode
- HTML/Markdown/PDF report generation
- Telegram bot integration
- Content quality and i18n checks
- Dashboard module
- Scheduler for periodic audits
