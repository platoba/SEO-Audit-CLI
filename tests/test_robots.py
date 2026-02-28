"""Tests for audit.checks.robots - robots.txt analysis."""

import pytest
from unittest.mock import MagicMock, patch
from audit.core import AuditResult, HTMLAnalyzer
from audit.checks.robots import RobotsCheck, RobotsAnalyzer


@pytest.fixture
def check():
    return RobotsCheck()


def _make_result():
    return AuditResult(url="https://example.com", domain="example.com")


def _make_analyzer():
    a = HTMLAnalyzer()
    a.set_domain("example.com")
    return a


class TestRobotsAnalyzer:
    def test_parse_basic(self):
        content = "User-agent: *\nDisallow: /admin/\nDisallow: /private/\nAllow: /admin/public/"
        ra = RobotsAnalyzer(content)
        assert "*" in ra.rules
        assert ra.disallow_count == 2
        assert "/admin/" in ra.blocked_paths

    def test_parse_sitemaps(self):
        content = "User-agent: *\nDisallow:\nSitemap: https://example.com/sitemap.xml\nSitemap: https://example.com/sitemap2.xml"
        ra = RobotsAnalyzer(content)
        assert len(ra.sitemaps) == 2
        assert "https://example.com/sitemap.xml" in ra.sitemaps

    def test_crawl_delay(self):
        content = "User-agent: Googlebot\nCrawl-delay: 5"
        ra = RobotsAnalyzer(content)
        assert ra.crawl_delay.get("Googlebot") == 5.0

    def test_host_directive(self):
        content = "User-agent: *\nDisallow:\nHost: www.example.com"
        ra = RobotsAnalyzer(content)
        assert ra.host == "www.example.com"

    def test_is_path_blocked(self):
        content = "User-agent: *\nDisallow: /admin/\nAllow: /admin/public/"
        ra = RobotsAnalyzer(content)
        assert not ra.is_path_blocked("/admin/public/page")
        assert ra.is_path_blocked("/admin/secret")

    def test_empty_disallow(self):
        content = "User-agent: *\nDisallow:"
        ra = RobotsAnalyzer(content)
        assert ra.disallow_count == 0

    def test_multiple_agents(self):
        content = "User-agent: Googlebot\nDisallow: /x\nUser-agent: Bingbot\nDisallow: /y"
        ra = RobotsAnalyzer(content)
        assert "Googlebot" in ra.rules
        assert "Bingbot" in ra.rules

    def test_comments_ignored(self):
        content = "# comment\nUser-agent: *\n# another\nDisallow: /test"
        ra = RobotsAnalyzer(content)
        assert ra.disallow_count == 1

    def test_total_rules(self):
        content = "User-agent: *\nDisallow: /a\nAllow: /b\nDisallow: /c"
        ra = RobotsAnalyzer(content)
        assert ra.total_rules == 3


class TestRobotsCheck:
    def test_robots_exists(self, check):
        result = _make_result()
        analyzer = _make_analyzer()
        resp = MagicMock()
        resp.text = "<html></html>"

        with patch("audit.checks.robots.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.ok = True
            mock_resp.text = "User-agent: *\nDisallow: /private/\nSitemap: https://example.com/sitemap.xml"
            mock_get.return_value = mock_resp
            check.run(result, resp, analyzer)

        assert result.details.get("robots", {}).get("exists") is True
        passed = [i.message for i in result.passed]
        assert any("robots.txt" in p for p in passed)

    def test_robots_not_found(self, check):
        result = _make_result()
        analyzer = _make_analyzer()
        resp = MagicMock()
        resp.text = "<html></html>"

        with patch("audit.checks.robots.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.ok = False
            mock_resp.status_code = 404
            mock_get.return_value = mock_resp
            check.run(result, resp, analyzer)

        assert result.details.get("robots", {}).get("exists") is False
        warnings = [i.message for i in result.warnings]
        assert any("不存在" in w for w in warnings)

    def test_robots_blocks_root(self, check):
        result = _make_result()
        analyzer = _make_analyzer()
        resp = MagicMock()
        resp.text = "<html></html>"

        with patch("audit.checks.robots.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.ok = True
            mock_resp.text = "User-agent: *\nDisallow: /"
            mock_get.return_value = mock_resp
            check.run(result, resp, analyzer)

        errors = [i.message for i in result.errors]
        assert any("根路径" in e for e in errors)

    def test_robots_empty(self, check):
        result = _make_result()
        analyzer = _make_analyzer()
        resp = MagicMock()
        resp.text = "<html></html>"

        with patch("audit.checks.robots.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.ok = True
            mock_resp.text = ""
            mock_get.return_value = mock_resp
            check.run(result, resp, analyzer)

        warnings = [i.message for i in result.warnings]
        assert any("空" in w for w in warnings)

    def test_robots_no_sitemap(self, check):
        result = _make_result()
        analyzer = _make_analyzer()
        resp = MagicMock()
        resp.text = "<html></html>"

        with patch("audit.checks.robots.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.ok = True
            mock_resp.text = "User-agent: *\nDisallow: /admin/"
            mock_get.return_value = mock_resp
            check.run(result, resp, analyzer)

        warnings = [i.message for i in result.warnings]
        assert any("sitemap" in w.lower() for w in warnings)

    def test_robots_timeout(self, check):
        result = _make_result()
        analyzer = _make_analyzer()
        resp = MagicMock()
        resp.text = "<html></html>"

        import requests as req
        with patch("audit.checks.robots.requests.get", side_effect=req.exceptions.Timeout):
            check.run(result, resp, analyzer)

        warnings = [i.message for i in result.warnings]
        assert any("超时" in w for w in warnings)
