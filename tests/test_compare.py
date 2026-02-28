"""Tests for audit.compare - competitor comparison."""

import pytest
from unittest.mock import patch, MagicMock
from audit.compare import compare_sites, format_comparison_text, _determine_winner, _cmp_row
from audit.core import AuditResult, AuditEngine


@pytest.fixture
def result_a():
    r = AuditResult(url="https://a.com", domain="a.com")
    r.score = 85
    r.load_time = 1.0
    r.details = {"page_size_kb": 200, "internal_links": 10, "external_links": 5,
                 "sitemap": True, "security_headers": {"present": ["HSTS", "CSP"], "missing": []}}
    r.add_issue("error", "meta", "err", 5)
    r.add_pass("sec", "ok")
    return r


@pytest.fixture
def result_b():
    r = AuditResult(url="https://b.com", domain="b.com")
    r.score = 70
    r.load_time = 2.5
    r.details = {"page_size_kb": 500, "internal_links": 3, "external_links": 20,
                 "sitemap": False, "security_headers": {"present": ["HSTS"], "missing": ["CSP"]}}
    r.add_issue("error", "meta", "err1", 5)
    r.add_issue("error", "links", "err2", 5)
    r.add_pass("sec", "ok")
    return r


class TestDetermineWinner:
    def test_overall_winner(self, result_a, result_b):
        w = _determine_winner(result_a, result_b)
        assert w["overall"] == "https://a.com"

    def test_speed_winner(self, result_a, result_b):
        w = _determine_winner(result_a, result_b)
        assert w["speed"] == "https://a.com"

    def test_errors_winner(self, result_a, result_b):
        w = _determine_winner(result_a, result_b)
        assert w["errors"] == "https://a.com"

    def test_tie(self):
        r1 = AuditResult(url="https://a.com", domain="a.com")
        r2 = AuditResult(url="https://b.com", domain="b.com")
        r1.score = 80
        r2.score = 80
        r1.load_time = 1.0
        r2.load_time = 1.0
        w = _determine_winner(r1, r2)
        assert w["overall"] == "tie"
        assert w["speed"] == "tie"


class TestCmpRow:
    def test_higher_better(self):
        row = _cmp_row("Score", 90, 80, higher_better=True)
        assert row["winner"] == "a"

    def test_lower_better(self):
        row = _cmp_row("Load Time", 1.0, 2.0, higher_better=False)
        assert row["winner"] == "a"

    def test_tie(self):
        row = _cmp_row("Score", 80, 80, higher_better=True)
        assert row["winner"] == "tie"

    def test_no_comparison(self):
        row = _cmp_row("Grade", "A", "B")
        assert row["winner"] == "tie"


class TestCompareSites:
    @patch("audit.core.requests.get")
    def test_compare_returns_structure(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "<html><head><title>Test</title></head><body></body></html>"
        resp.content = resp.text.encode()
        resp.headers = {}
        mock_get.return_value = resp

        comparison = compare_sites("https://a.com", "https://b.com", engine=AuditEngine(checks=[], timeout=5))
        assert "site_a" in comparison
        assert "site_b" in comparison
        assert "winner" in comparison
        assert "comparison" in comparison


class TestFormatComparison:
    def test_format_text(self, result_a, result_b):
        comparison = {
            "site_a": result_a.to_dict(),
            "site_b": result_b.to_dict(),
            "winner": _determine_winner(result_a, result_b),
            "comparison": [],
        }
        text = format_comparison_text(comparison)
        assert "Competitor Comparison" in text
        assert "a.com" in text
        assert "b.com" in text

    def test_format_with_winner(self, result_a, result_b):
        from audit.compare import _build_comparison
        comparison = {
            "site_a": result_a.to_dict(),
            "site_b": result_b.to_dict(),
            "winner": _determine_winner(result_a, result_b),
            "comparison": _build_comparison(result_a, result_b),
        }
        text = format_comparison_text(comparison)
        assert "Winner" in text
