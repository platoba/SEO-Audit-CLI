"""Tests for audit.checks.redirect - redirect chain analysis."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from audit.core import AuditResult, HTMLAnalyzer
from audit.checks.redirect import RedirectCheck, RedirectChainAnalyzer


@pytest.fixture
def check():
    return RedirectCheck()


def _make_result():
    return AuditResult(url="https://example.com", domain="example.com")


def _make_analyzer(html="<html><head></head><body></body></html>"):
    a = HTMLAnalyzer()
    a.set_domain("example.com")
    a.feed(html)
    return a


class TestRedirectChainAnalyzer:
    def test_no_redirect(self):
        with patch("audit.checks.redirect.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.headers = {}
            mock_get.return_value = mock_resp

            rca = RedirectChainAnalyzer("https://example.com").trace()
            assert rca.hop_count == 0
            assert rca.final_url == "https://example.com"

    def test_single_redirect(self):
        with patch("audit.checks.redirect.requests.get") as mock_get:
            responses = [
                MagicMock(status_code=301, headers={"Location": "https://www.example.com"}),
                MagicMock(status_code=200, headers={}),
            ]
            mock_get.side_effect = responses

            rca = RedirectChainAnalyzer("https://example.com").trace()
            assert rca.hop_count == 1
            assert len(rca.chain) == 2

    def test_chain_detection(self):
        with patch("audit.checks.redirect.requests.get") as mock_get:
            responses = [
                MagicMock(status_code=301, headers={"Location": "https://a.com"}),
                MagicMock(status_code=302, headers={"Location": "https://b.com"}),
                MagicMock(status_code=301, headers={"Location": "https://c.com"}),
                MagicMock(status_code=200, headers={}),
            ]
            mock_get.side_effect = responses

            rca = RedirectChainAnalyzer("https://example.com").trace()
            assert rca.hop_count == 3
            assert rca.has_temporary_redirects is True

    def test_loop_detection(self):
        with patch("audit.checks.redirect.requests.get") as mock_get:
            mock_resp = MagicMock(status_code=301, headers={"Location": "https://example.com"})
            mock_get.return_value = mock_resp

            rca = RedirectChainAnalyzer("https://example.com").trace()
            assert rca.has_loop is True

    def test_mixed_protocol(self):
        with patch("audit.checks.redirect.requests.get") as mock_get:
            responses = [
                MagicMock(status_code=301, headers={"Location": "https://example.com"}),
                MagicMock(status_code=200, headers={}),
            ]
            mock_get.side_effect = responses

            rca = RedirectChainAnalyzer("http://example.com").trace()
            assert rca.has_mixed_protocol is True

    def test_permanent_only(self):
        with patch("audit.checks.redirect.requests.get") as mock_get:
            responses = [
                MagicMock(status_code=301, headers={"Location": "https://www.example.com"}),
                MagicMock(status_code=200, headers={}),
            ]
            mock_get.side_effect = responses

            rca = RedirectChainAnalyzer("https://example.com").trace()
            assert rca.permanent_only is True


class TestRedirectCheck:
    def test_no_redirects(self, check):
        result = _make_result()
        analyzer = _make_analyzer()
        resp = MagicMock()
        resp.history = []
        resp.url = "https://example.com"

        check.run(result, resp, analyzer)
        passed = [i.message for i in result.passed]
        assert any("无重定向" in p for p in passed)

    def test_single_301_redirect(self, check):
        result = _make_result()
        analyzer = _make_analyzer()
        redirect = MagicMock()
        redirect.url = "http://example.com"
        redirect.status_code = 301
        resp = MagicMock()
        resp.history = [redirect]
        resp.url = "https://example.com"

        check.run(result, resp, analyzer)
        passed = [i.message for i in result.passed]
        assert any("301" in p for p in passed)

    def test_temporary_redirect_warning(self, check):
        result = _make_result()
        analyzer = _make_analyzer()
        redirect = MagicMock()
        redirect.url = "http://example.com"
        redirect.status_code = 302
        resp = MagicMock()
        resp.history = [redirect]
        resp.url = "https://example.com"

        check.run(result, resp, analyzer)
        warnings = [i.message for i in result.warnings]
        assert any("临时重定向" in w for w in warnings)

    def test_long_chain_error(self, check):
        result = _make_result()
        analyzer = _make_analyzer()
        redirects = []
        for i in range(4):
            r = MagicMock()
            r.url = f"https://r{i}.example.com"
            r.status_code = 301
            redirects.append(r)
        resp = MagicMock()
        resp.history = redirects
        resp.url = "https://final.example.com"

        check.run(result, resp, analyzer)
        errors = [i.message for i in result.errors]
        assert any("过长" in e for e in errors)

    def test_mixed_protocol_warning(self, check):
        result = _make_result()
        analyzer = _make_analyzer()
        redirect = MagicMock()
        redirect.url = "http://example.com"
        redirect.status_code = 301
        resp = MagicMock()
        resp.history = [redirect]
        resp.url = "https://example.com"

        check.run(result, resp, analyzer)
        warnings = [i.message for i in result.warnings]
        assert any("混合协议" in w for w in warnings)

    def test_canonical_mismatch(self, check):
        result = _make_result()
        html = '<html><head><meta property="canonical" content="https://other.com"></head><body></body></html>'
        analyzer = _make_analyzer(html)
        resp = MagicMock()
        resp.history = []
        resp.url = "https://example.com"

        check.run(result, resp, analyzer)
        warnings = [i.message for i in result.warnings]
        assert any("canonical" in w for w in warnings)
