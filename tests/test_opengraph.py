"""Tests for audit.checks.opengraph - Open Graph & Twitter Card validation."""

import pytest
from unittest.mock import MagicMock
from audit.core import AuditResult, HTMLAnalyzer
from audit.checks.opengraph import OpenGraphCheck


@pytest.fixture
def check():
    return OpenGraphCheck()


def _make_result():
    return AuditResult(url="https://example.com", domain="example.com")


def _run(check, html):
    result = _make_result()
    analyzer = HTMLAnalyzer()
    analyzer.set_domain("example.com")
    analyzer.feed(html)
    resp = MagicMock()
    resp.text = html
    check.run(result, resp, analyzer)
    return result


class TestOpenGraphCheck:
    def test_complete_og_tags(self, check):
        html = """<html><head>
        <meta property="og:title" content="Test Page">
        <meta property="og:description" content="A test description">
        <meta property="og:image" content="https://example.com/img.jpg">
        <meta property="og:url" content="https://example.com">
        <meta property="og:type" content="website">
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="Test">
        <meta name="twitter:description" content="Desc">
        <meta name="twitter:image" content="https://example.com/img.jpg">
        </head><body></body></html>"""
        result = _run(check, html)
        passed = [i.message for i in result.passed]
        assert any("Open Graph" in p and "完整" in p for p in passed)

    def test_missing_all_og_tags(self, check):
        html = "<html><head></head><body></body></html>"
        result = _run(check, html)
        errors = [i.message for i in result.errors]
        assert any("Open Graph" in e for e in errors)

    def test_missing_some_og_tags(self, check):
        html = """<html><head>
        <meta property="og:title" content="Test">
        </head><body></body></html>"""
        result = _run(check, html)
        warnings = [i.message for i in result.warnings]
        assert any("OG必要标签" in w for w in warnings)

    def test_og_title_too_long(self, check):
        long_title = "x" * 100
        html = f"""<html><head>
        <meta property="og:title" content="{long_title}">
        <meta property="og:description" content="desc">
        <meta property="og:image" content="https://example.com/img.jpg">
        <meta property="og:url" content="https://example.com">
        <meta property="og:type" content="website">
        </head><body></body></html>"""
        result = _run(check, html)
        warnings = [i.message for i in result.warnings]
        assert any("og:title过长" in w for w in warnings)

    def test_og_image_relative_url(self, check):
        html = """<html><head>
        <meta property="og:title" content="Test">
        <meta property="og:description" content="desc">
        <meta property="og:image" content="/images/test.jpg">
        <meta property="og:url" content="https://example.com">
        <meta property="og:type" content="website">
        </head><body></body></html>"""
        result = _run(check, html)
        warnings = [i.message for i in result.warnings]
        assert any("完整URL" in w for w in warnings)

    def test_missing_og_image(self, check):
        html = """<html><head>
        <meta property="og:title" content="Test">
        <meta property="og:description" content="desc">
        <meta property="og:url" content="https://example.com">
        <meta property="og:type" content="website">
        </head><body></body></html>"""
        result = _run(check, html)
        warnings = [i.message for i in result.warnings]
        assert any("og:image" in w for w in warnings)

    def test_missing_twitter_cards(self, check):
        html = """<html><head>
        <meta property="og:title" content="Test">
        </head><body></body></html>"""
        result = _run(check, html)
        warnings = [i.message for i in result.warnings]
        assert any("Twitter Card" in w for w in warnings)

    def test_invalid_twitter_card_type(self, check):
        html = """<html><head>
        <meta name="twitter:card" content="invalid_type">
        <meta name="twitter:title" content="Test">
        </head><body></body></html>"""
        result = _run(check, html)
        warnings = [i.message for i in result.warnings]
        assert any("twitter:card" in w and "无效" in w for w in warnings)

    def test_valid_twitter_card(self, check):
        html = """<html><head>
        <meta name="twitter:card" content="summary">
        <meta name="twitter:title" content="Test">
        <meta name="twitter:description" content="Desc">
        <meta name="twitter:image" content="https://example.com/img.jpg">
        </head><body></body></html>"""
        result = _run(check, html)
        passed = [i.message for i in result.passed]
        assert any("Twitter Card" in p for p in passed)

    def test_og_details_in_result(self, check):
        html = """<html><head>
        <meta property="og:title" content="Test">
        <meta property="og:type" content="website">
        </head><body></body></html>"""
        result = _run(check, html)
        assert "opengraph" in result.details
        assert "og_tags" in result.details["opengraph"]
        assert "twitter_tags" in result.details["opengraph"]
