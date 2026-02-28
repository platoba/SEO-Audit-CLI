"""Tests for audit.checks.performance - status, load time, page size, CWV, caching."""

import pytest
from unittest.mock import MagicMock
from audit.core import AuditResult, HTMLAnalyzer
from audit.checks.performance import PerformanceCheck


@pytest.fixture
def check():
    return PerformanceCheck()


def _make_resp(html, status=200, headers=None, content_size=None):
    resp = MagicMock()
    resp.status_code = status
    resp.text = html
    if content_size:
        resp.content = b"x" * content_size
    else:
        resp.content = html.encode()
    resp.headers = headers or {}
    return resp


def _run(check, result, html, status=200, headers=None, content_size=None):
    analyzer = HTMLAnalyzer()
    analyzer.set_domain("example.com")
    analyzer.feed(html)
    resp = _make_resp(html, status, headers, content_size)
    check.run(result, resp, analyzer)
    return result


class TestPerformanceCheck:
    def test_status_200_pass(self, check, result_template):
        r = _run(check, result_template, "<html></html>", 200, {"Content-Encoding": "gzip"})
        passed = [i.message for i in r.passed]
        assert any("200" in p for p in passed)

    def test_status_404_error(self, check, result_template):
        r = _run(check, result_template, "<html></html>", 404)
        errors = [i.message for i in r.errors]
        assert any("404" in e for e in errors)

    def test_slow_load_time(self, check, result_template):
        result_template.load_time = 4.0
        r = _run(check, result_template, "<html></html>")
        warnings = [i.message for i in r.warnings]
        assert any("加载时间" in w or "load" in w.lower() for w in warnings)

    def test_very_slow_load_time(self, check, result_template):
        result_template.load_time = 6.0
        r = _run(check, result_template, "<html></html>")
        errors = [i.message for i in r.errors]
        assert any("加载时间" in e for e in errors)

    def test_fast_load_pass(self, check, result_template):
        result_template.load_time = 0.5
        r = _run(check, result_template, "<html></html>", headers={"Content-Encoding": "gzip"})
        passed = [i.message for i in r.passed]
        assert any("加载速度" in p or "速度" in p for p in passed)

    def test_large_page_warning(self, check, result_template):
        r = _run(check, result_template, "<html></html>", content_size=1500 * 1024)
        warnings = [i.message for i in r.warnings]
        assert any("页面较大" in w for w in warnings)

    def test_very_large_page_error(self, check, result_template):
        r = _run(check, result_template, "<html></html>", content_size=4000 * 1024)
        errors = [i.message for i in r.errors]
        assert any("页面过大" in e for e in errors)

    def test_compression_detected(self, check, result_template):
        r = _run(check, result_template, "<html></html>", headers={"Content-Encoding": "br"})
        passed = [i.message for i in r.passed]
        assert any("压缩" in p for p in passed)

    def test_no_compression_warning(self, check, result_template):
        r = _run(check, result_template, "<html></html>", headers={})
        warnings = [i.message for i in r.warnings]
        assert any("压缩" in w for w in warnings)

    def test_cache_control_present(self, check, result_template):
        r = _run(check, result_template, "<html></html>", headers={"Cache-Control": "max-age=3600", "Content-Encoding": "gzip"})
        passed = [i.message for i in r.passed]
        assert any("Cache-Control" in p for p in passed)

    def test_too_many_scripts_warning(self, check, result_template):
        scripts = ''.join(f'<script src="s{i}.js"></script>' for i in range(25))
        html = f'<html><head>{scripts}</head><body></body></html>'
        r = _run(check, result_template, html, headers={"Content-Encoding": "gzip"})
        warnings = [i.message for i in r.warnings]
        assert any("JS" in w for w in warnings)

    def test_render_blocking_scripts(self, check, result_template):
        html = '<html><head><script src="a.js"></script><script src="b.js"></script></head><body></body></html>'
        r = _run(check, result_template, html, headers={"Content-Encoding": "gzip"})
        warnings = [i.message for i in r.warnings]
        assert any("阻塞" in w or "blocking" in w.lower() for w in warnings)

    def test_cwv_lcp_good(self, check, result_template):
        result_template.load_time = 1.0
        r = _run(check, result_template, "<html><body></body></html>", headers={"Content-Encoding": "gzip"})
        assert r.details.get("core_web_vitals", {}).get("LCP", {}).get("status") == "good"

    def test_cwv_lcp_poor(self, check, result_template):
        result_template.load_time = 5.0
        r = _run(check, result_template, "<html><body></body></html>")
        assert r.details.get("core_web_vitals", {}).get("LCP", {}).get("status") == "poor"

    def test_cwv_cls_risk(self, check, result_template):
        imgs = ''.join(f'<img src="{i}.jpg">' for i in range(5))
        html = f'<html><body>{imgs}</body></html>'
        r = _run(check, result_template, html, headers={"Content-Encoding": "gzip"})
        cls = r.details.get("core_web_vitals", {}).get("CLS", {})
        assert cls.get("status") in ("needs_improvement", "poor")
