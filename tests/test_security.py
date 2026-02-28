"""Tests for audit.checks.security - HTTPS, headers, mixed content, server info."""

import pytest
from unittest.mock import MagicMock
from audit.core import AuditResult, HTMLAnalyzer
from audit.checks.security import SecurityCheck


@pytest.fixture
def check():
    return SecurityCheck()


def _run(check, result, html, headers=None, url=None):
    if url:
        result.url = url
    analyzer = HTMLAnalyzer()
    analyzer.set_domain(result.domain)
    analyzer.feed(html)
    resp = MagicMock()
    resp.status_code = 200
    resp.text = html
    resp.content = html.encode()
    resp.headers = headers or {}
    check.run(result, resp, analyzer)
    return result


class TestSecurityCheck:
    def test_https_pass(self, check, result_template):
        r = _run(check, result_template, "<html></html>", headers=_all_sec_headers())
        passed = [i.message for i in r.passed]
        assert any("HTTPS" in p for p in passed)

    def test_http_error(self, check, result_template):
        result_template.url = "http://example.com"
        r = _run(check, result_template, "<html></html>", url="http://example.com")
        errors = [i.message for i in r.errors]
        assert any("HTTPS" in e for e in errors)

    def test_all_security_headers_pass(self, check, result_template):
        r = _run(check, result_template, "<html></html>", headers=_all_sec_headers())
        passed = [i.message for i in r.passed]
        assert any("安全头" in p or "HSTS" in p for p in passed)

    def test_missing_security_headers(self, check, result_template):
        r = _run(check, result_template, "<html></html>", headers={})
        warnings = [i.message for i in r.warnings]
        assert any("安全头" in w for w in warnings)

    def test_mixed_content_detected(self, check, result_template, mixed_html):
        r = _run(check, result_template, mixed_html, headers=_all_sec_headers())
        warnings = [i.message for i in r.warnings]
        assert any("混合内容" in w for w in warnings)

    def test_no_mixed_content(self, check, result_template, perfect_html):
        r = _run(check, result_template, perfect_html, headers=_all_sec_headers())
        passed = [i.message for i in r.passed]
        assert any("混合内容" in p for p in passed)

    def test_server_header_exposed(self, check, result_template):
        r = _run(check, result_template, "<html></html>", headers={"Server": "nginx/1.19", **_all_sec_headers()})
        info = [i for i in r.issues if i.severity == "info"]
        assert any("Server" in i.message for i in info)

    def test_x_powered_by_exposed(self, check, result_template):
        r = _run(check, result_template, "<html></html>", headers={"X-Powered-By": "PHP/8.1", **_all_sec_headers()})
        warnings = [i.message for i in r.warnings]
        assert any("X-Powered-By" in w for w in warnings)

    def test_security_headers_detail(self, check, result_template):
        r = _run(check, result_template, "<html></html>", headers={
            "Strict-Transport-Security": "max-age=31536000",
            "X-Content-Type-Options": "nosniff",
        })
        sec = r.details.get("security_headers", {})
        assert "Strict-Transport-Security" in sec.get("present", [])
        assert "Content-Security-Policy" in sec.get("missing", [])


def _all_sec_headers():
    return {
        "Strict-Transport-Security": "max-age=31536000",
        "Content-Security-Policy": "default-src 'self'",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=()",
    }
