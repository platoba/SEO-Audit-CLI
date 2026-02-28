"""Shared fixtures for SEO-Audit-CLI tests."""

import pytest
from unittest.mock import MagicMock
from audit.core import AuditResult, AuditEngine, HTMLAnalyzer


# ---------------------------------------------------------------------------
# Minimal HTML pages used across test modules
# ---------------------------------------------------------------------------

PERFECT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="A perfectly optimized page with all the right meta tags for SEO auditing purposes and best practices.">
<meta name="robots" content="index, follow">
<meta property="og:title" content="Perfect Page">
<meta property="og:description" content="A perfectly optimized page description for social sharing.">
<meta property="og:image" content="https://example.com/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="https://example.com/">
<title>Perfect Example Page - SEO Optimized</title>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"WebSite","name":"Example","url":"https://example.com"}
</script>
</head>
<body>
<a href="#main-content">Skip to main</a>
<nav role="navigation"><a href="/about">About</a><a href="/contact">Contact</a></nav>
<main id="main-content" role="main">
<h1>Welcome to the Perfect Page</h1>
<h2>Section One</h2>
<p>Some paragraph text with <a href="/internal-link">internal link</a>.</p>
<img src="hero.jpg" alt="Hero image" width="800" height="400" loading="lazy">
<img src="thumb.jpg" alt="Thumbnail" width="200" height="200" loading="lazy">
<h2>Section Two</h2>
<p>More content with <a href="https://othersite.org" rel="nofollow">external link</a>.</p>
<form><label for="email">Email</label><input id="email" type="email"></form>
</main>
</body>
</html>"""

MINIMAL_HTML = """<html><head><title>Hi</title></head><body><p>Hello</p></body></html>"""

BROKEN_HTML = """<html><head></head><body><img src="x.jpg"><a href="/no-text"></a></body></html>"""

HTTP_MIXED_HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta name="viewport" content="width=device-width"><title>Mixed Content Page Title OK</title>
<meta name="description" content="This page has mixed content issues where some resources load over HTTP instead of HTTPS.">
</head>
<body>
<main><h1>Mixed Content</h1>
<img src="http://insecure.example.com/img.jpg" alt="insecure" width="100" height="100">
<script src="http://insecure.example.com/evil.js"></script>
</main>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def perfect_html():
    return PERFECT_HTML


@pytest.fixture
def minimal_html():
    return MINIMAL_HTML


@pytest.fixture
def broken_html():
    return BROKEN_HTML


@pytest.fixture
def mixed_html():
    return HTTP_MIXED_HTML


@pytest.fixture
def analyzer_perfect():
    """Pre-parsed HTMLAnalyzer for the perfect page."""
    a = HTMLAnalyzer()
    a.set_domain("example.com")
    a.feed(PERFECT_HTML)
    return a


@pytest.fixture
def analyzer_minimal():
    a = HTMLAnalyzer()
    a.set_domain("example.com")
    a.feed(MINIMAL_HTML)
    return a


@pytest.fixture
def analyzer_broken():
    a = HTMLAnalyzer()
    a.set_domain("example.com")
    a.feed(BROKEN_HTML)
    return a


@pytest.fixture
def result_template():
    """Fresh AuditResult for unit testing checks."""
    return AuditResult(url="https://example.com", domain="example.com")


@pytest.fixture
def mock_response_200(perfect_html):
    """Mock requests.Response (200, perfect HTML)."""
    resp = MagicMock()
    resp.status_code = 200
    resp.text = perfect_html
    resp.content = perfect_html.encode()
    resp.headers = {
        "Content-Encoding": "gzip",
        "Cache-Control": "max-age=3600",
        "Strict-Transport-Security": "max-age=31536000",
        "Content-Security-Policy": "default-src 'self'",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=()",
    }
    return resp


@pytest.fixture
def mock_response_broken(broken_html):
    resp = MagicMock()
    resp.status_code = 200
    resp.text = broken_html
    resp.content = broken_html.encode()
    resp.headers = {}
    return resp


@pytest.fixture
def mock_response_mixed(mixed_html):
    resp = MagicMock()
    resp.status_code = 200
    resp.text = mixed_html
    resp.content = mixed_html.encode()
    resp.headers = {
        "Content-Encoding": "gzip",
    }
    return resp
