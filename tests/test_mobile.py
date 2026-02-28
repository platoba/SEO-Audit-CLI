"""Tests for audit.checks.mobile - viewport, robots, sitemap, resources."""

import pytest
from unittest.mock import MagicMock, patch
from audit.core import AuditResult, HTMLAnalyzer
from audit.checks.mobile import MobileCheck


@pytest.fixture
def check():
    return MobileCheck()


def _run(check, result, html, robots_ok=True, sitemap_ok=True):
    analyzer = HTMLAnalyzer()
    analyzer.set_domain("example.com")
    analyzer.feed(html)
    resp = MagicMock()
    resp.status_code = 200
    resp.text = html
    resp.content = html.encode()
    resp.headers = {}

    with patch("audit.checks.mobile.requests.get") as mock_get:
        def side_effect(url, **kwargs):
            r = MagicMock()
            if "robots.txt" in url:
                r.ok = robots_ok
                r.text = "User-agent: *\nDisallow:" if robots_ok else ""
            elif "sitemap.xml" in url:
                r.ok = sitemap_ok
                r.text = '<?xml version="1.0"?><urlset></urlset>' if sitemap_ok else ""
            return r

        mock_get.side_effect = side_effect
        check.run(result, resp, analyzer)
    return result


class TestMobileCheck:
    def test_viewport_pass(self, check, result_template):
        html = '<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head><body></body></html>'
        r = _run(check, result_template, html)
        passed = [i.message for i in r.passed]
        assert any("viewport" in p for p in passed)

    def test_missing_viewport_error(self, check, result_template):
        html = '<html><head></head><body></body></html>'
        r = _run(check, result_template, html)
        errors = [i.message for i in r.errors]
        assert any("viewport" in e for e in errors)

    def test_viewport_missing_device_width(self, check, result_template):
        html = '<html><head><meta name="viewport" content="initial-scale=1.0"></head><body></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("device-width" in w for w in warnings)

    def test_small_font_warning(self, check, result_template):
        html = '<html><head><meta name="viewport" content="width=device-width"></head><body><p style="font-size:8px">tiny</p></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("字体" in w or "font" in w.lower() for w in warnings)

    def test_robots_txt_exists(self, check, result_template):
        html = '<html><head><meta name="viewport" content="width=device-width"></head><body></body></html>'
        r = _run(check, result_template, html, robots_ok=True)
        passed = [i.message for i in r.passed]
        assert any("robots.txt" in p for p in passed)

    def test_robots_txt_missing(self, check, result_template):
        html = '<html><head><meta name="viewport" content="width=device-width"></head><body></body></html>'
        r = _run(check, result_template, html, robots_ok=False)
        warnings = [i.message for i in r.warnings]
        assert any("robots.txt" in w for w in warnings)

    def test_sitemap_exists(self, check, result_template):
        html = '<html><head><meta name="viewport" content="width=device-width"></head><body></body></html>'
        r = _run(check, result_template, html, sitemap_ok=True)
        passed = [i.message for i in r.passed]
        assert any("sitemap" in p.lower() for p in passed)

    def test_sitemap_missing(self, check, result_template):
        html = '<html><head><meta name="viewport" content="width=device-width"></head><body></body></html>'
        r = _run(check, result_template, html, sitemap_ok=False)
        warnings = [i.message for i in r.warnings]
        assert any("sitemap" in w.lower() for w in warnings)

    def test_too_many_resources(self, check, result_template):
        scripts = ''.join(f'<script src="s{i}.js"></script>' for i in range(20))
        css = ''.join(f'<link rel="stylesheet" href="c{i}.css">' for i in range(15))
        html = f'<html><head><meta name="viewport" content="width=device-width">{scripts}{css}</head><body></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("资源" in w for w in warnings)

    def test_too_many_links(self, check, result_template):
        links = ''.join(f'<a href="/p{i}">p{i}</a>' for i in range(250))
        html = f'<html><head><meta name="viewport" content="width=device-width"></head><body>{links}</body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("链接" in w or "点击" in w for w in warnings)
