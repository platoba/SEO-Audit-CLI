"""Tests for audit.core: AuditResult, AuditIssue, HTMLAnalyzer, AuditEngine."""

import pytest
from unittest.mock import patch, MagicMock

from audit.core import AuditResult, AuditIssue, HTMLAnalyzer, AuditEngine


# ---------------------------------------------------------------------------
# AuditIssue
# ---------------------------------------------------------------------------

class TestAuditIssue:
    def test_create(self):
        issue = AuditIssue(severity="error", category="meta", message="Missing title", deduction=10)
        assert issue.severity == "error"
        assert issue.category == "meta"
        assert issue.deduction == 10

    def test_default_deduction(self):
        issue = AuditIssue(severity="info", category="links", message="No external links")
        assert issue.deduction == 0


# ---------------------------------------------------------------------------
# AuditResult
# ---------------------------------------------------------------------------

class TestAuditResult:
    def test_initial_score(self, result_template):
        assert result_template.score == 100

    def test_add_issue_deducts(self, result_template):
        result_template.add_issue("error", "meta", "bad", 10)
        assert result_template.score == 90
        assert len(result_template.errors) == 1

    def test_add_pass(self, result_template):
        result_template.add_pass("meta", "title OK")
        assert len(result_template.passed) == 1
        assert result_template.score == 100

    def test_score_cannot_go_below_zero(self, result_template):
        for _ in range(20):
            result_template.add_issue("error", "x", "x", 10)
        assert result_template.score == 0

    @pytest.mark.parametrize("score,expected", [
        (100, "A+"), (95, "A+"), (94, "A"), (90, "A"),
        (89, "B"), (80, "B"), (79, "C"), (70, "C"),
        (69, "D"), (60, "D"), (59, "F"), (0, "F"),
    ])
    def test_grade(self, result_template, score, expected):
        result_template.score = score
        assert result_template.grade == expected

    def test_to_dict(self, result_template):
        result_template.add_issue("error", "meta", "err", 5)
        result_template.add_issue("warning", "links", "warn", 2)
        result_template.add_pass("perf", "ok")
        d = result_template.to_dict()
        assert d["error_count"] == 1
        assert d["warning_count"] == 1
        assert d["pass_count"] == 1
        assert d["grade"] == "A"

    def test_errors_property(self, result_template):
        result_template.add_issue("error", "a", "e1", 1)
        result_template.add_issue("warning", "a", "w1", 1)
        result_template.add_issue("error", "a", "e2", 1)
        assert len(result_template.errors) == 2
        assert len(result_template.warnings) == 1


# ---------------------------------------------------------------------------
# HTMLAnalyzer
# ---------------------------------------------------------------------------

class TestHTMLAnalyzer:
    def test_title_extraction(self, analyzer_perfect):
        assert "Perfect Example Page" in analyzer_perfect.title

    def test_meta_description(self, analyzer_perfect):
        assert "perfectly optimized" in analyzer_perfect.meta.get("description", "")

    def test_headings(self, analyzer_perfect):
        assert len(analyzer_perfect.headings["h1"]) == 1
        assert len(analyzer_perfect.headings["h2"]) == 2

    def test_images(self, analyzer_perfect):
        assert len(analyzer_perfect.images) == 2
        assert all(img["alt"] for img in analyzer_perfect.images)

    def test_images_lazy_loading(self, analyzer_perfect):
        lazy = [img for img in analyzer_perfect.images if img["loading"] == "lazy"]
        assert len(lazy) == 2

    def test_internal_links(self, analyzer_perfect):
        assert len(analyzer_perfect.links["internal"]) >= 3

    def test_external_links(self, analyzer_perfect):
        assert len(analyzer_perfect.links["external"]) >= 1

    def test_json_ld_parsed(self, analyzer_perfect):
        assert len(analyzer_perfect.json_ld) >= 1

    def test_lang_attribute(self, analyzer_perfect):
        assert analyzer_perfect.lang == "en"

    def test_main_landmark(self, analyzer_perfect):
        assert analyzer_perfect.has_main_landmark is True

    def test_nav_landmark(self, analyzer_perfect):
        assert analyzer_perfect.has_nav_landmark is True

    def test_skip_link(self, analyzer_perfect):
        assert analyzer_perfect.has_skip_link is True

    def test_form_labels(self, analyzer_perfect):
        assert analyzer_perfect.form_labels >= 1

    def test_minimal_html(self, analyzer_minimal):
        assert analyzer_minimal.title == "Hi"
        assert not analyzer_minimal.headings["h1"]

    def test_broken_html_no_alt(self, analyzer_broken):
        assert len(analyzer_broken.images) == 1
        assert analyzer_broken.images[0]["alt"] is None

    def test_doctype_detection(self, analyzer_perfect):
        assert analyzer_perfect.has_doctype is True

    def test_no_doctype(self, analyzer_minimal):
        assert analyzer_minimal.has_doctype is False

    def test_og_tags(self, analyzer_perfect):
        assert "og:title" in analyzer_perfect.meta
        assert "og:image" in analyzer_perfect.meta

    def test_twitter_card(self, analyzer_perfect):
        assert analyzer_perfect.meta.get("twitter:card") == "summary_large_image"

    def test_canonical_in_html(self, analyzer_perfect):
        assert 'canonical' in analyzer_perfect.html_raw.lower()

    def test_set_domain(self):
        a = HTMLAnalyzer()
        a.set_domain("test.com")
        assert a._base_domain == "test.com"

    def test_scripts_tracking(self):
        html = '<html><head><script src="a.js" async></script><script src="b.js"></script></head><body></body></html>'
        a = HTMLAnalyzer()
        a.set_domain("example.com")
        a.feed(html)
        assert len(a.scripts) == 2

    def test_stylesheets_tracking(self):
        html = '<html><head><link rel="stylesheet" href="a.css"><link rel="stylesheet" href="b.css"></head><body></body></html>'
        a = HTMLAnalyzer()
        a.set_domain("example.com")
        a.feed(html)
        assert len(a.stylesheets) == 2


# ---------------------------------------------------------------------------
# AuditEngine (unit, mocked HTTP)
# ---------------------------------------------------------------------------

class TestAuditEngine:
    @patch("audit.core.requests.get")
    def test_audit_returns_result(self, mock_get, mock_response_200, analyzer_perfect):
        mock_get.return_value = mock_response_200
        engine = AuditEngine(checks=[], timeout=5)
        result = engine.audit("https://example.com")
        assert isinstance(result, AuditResult)
        assert result.status_code == 200

    @patch("audit.core.requests.get")
    def test_audit_connection_failure(self, mock_get):
        mock_get.side_effect = ConnectionError("timeout")
        engine = AuditEngine(checks=[], timeout=5)
        result = engine.audit("https://unreachable.example.com")
        assert result.score == 0
        assert len(result.errors) >= 1

    @patch("audit.core.requests.get")
    def test_audit_prepends_https(self, mock_get, mock_response_200):
        mock_get.return_value = mock_response_200
        engine = AuditEngine(checks=[], timeout=5)
        result = engine.audit("example.com")
        assert result.url == "https://example.com"

    @patch("audit.core.requests.get")
    def test_audit_multiple(self, mock_get, mock_response_200):
        mock_get.return_value = mock_response_200
        engine = AuditEngine(checks=[], timeout=5)
        results = engine.audit_multiple(["https://a.com", "https://b.com"])
        assert len(results) == 2
