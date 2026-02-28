"""Tests for audit.reports - HTML, JSON, PDF report generators."""

import json
import os
import tempfile
import pytest
from audit.core import AuditResult
from audit.reports.html_report import generate_html_report, save_html_report
from audit.reports.json_report import generate_json_report, save_json_report
from audit.reports.pdf_report import save_pdf_report


@pytest.fixture
def sample_result():
    r = AuditResult(url="https://example.com", domain="example.com", timestamp="2026-02-28T00:00:00Z")
    r.load_time = 1.2
    r.status_code = 200
    r.add_issue("error", "meta", "Missing title", 10)
    r.add_issue("warning", "links", "No lazy loading", 2)
    r.add_pass("security", "HTTPS OK")
    r.details["page_size_kb"] = 150
    r.details["core_web_vitals"] = {"LCP": {"status": "good", "estimate": "1.2s"}}
    r.details["security_headers"] = {"present": ["HSTS"], "missing": ["CSP"]}
    return r


@pytest.fixture
def sample_batch():
    results = []
    for i in range(3):
        r = AuditResult(url=f"https://example{i}.com", domain=f"example{i}.com", timestamp="2026-02-28T00:00:00Z")
        r.score = 70 + i * 10
        r.load_time = 1.0 + i * 0.5
        r.add_issue("error", "meta", "err", 5)
        r.add_issue("warning", "links", "warn", 2)
        r.add_pass("sec", "ok")
        results.append(r)
    return results


class TestHTMLReport:
    def test_single_report_contains_url(self, sample_result):
        html = generate_html_report(sample_result)
        assert "example.com" in html

    def test_single_report_contains_score(self, sample_result):
        html = generate_html_report(sample_result)
        assert str(sample_result.score) in html

    def test_single_report_contains_issues(self, sample_result):
        html = generate_html_report(sample_result)
        assert "Missing title" in html
        assert "HTTPS OK" in html

    def test_single_report_contains_cwv(self, sample_result):
        html = generate_html_report(sample_result)
        assert "LCP" in html

    def test_single_report_contains_security(self, sample_result):
        html = generate_html_report(sample_result)
        assert "HSTS" in html

    def test_batch_report(self, sample_batch):
        html = generate_html_report(sample_batch)
        assert "Batch" in html
        for r in sample_batch:
            assert r.url in html

    def test_save_html_report(self, sample_result):
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            save_html_report(sample_result, path)
            assert os.path.exists(path)
            with open(path) as f:
                content = f.read()
            assert "example.com" in content
        finally:
            os.unlink(path)


class TestJSONReport:
    def test_single_report_valid_json(self, sample_result):
        output = generate_json_report(sample_result)
        data = json.loads(output)
        assert data["url"] == "https://example.com"
        assert "grade" in data

    def test_single_report_has_counts(self, sample_result):
        output = generate_json_report(sample_result)
        data = json.loads(output)
        assert data["error_count"] == 1
        assert data["warning_count"] == 1
        assert data["pass_count"] == 1

    def test_batch_report(self, sample_batch):
        output = generate_json_report(sample_batch)
        data = json.loads(output)
        assert data["report_type"] == "batch_audit"
        assert data["total_urls"] == 3
        assert "summary" in data
        assert len(data["results"]) == 3

    def test_batch_summary(self, sample_batch):
        output = generate_json_report(sample_batch)
        data = json.loads(output)
        summary = data["summary"]
        assert "avg_score" in summary
        assert "min_score" in summary
        assert "max_score" in summary

    def test_save_json_report(self, sample_result):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_json_report(sample_result, path)
            assert os.path.exists(path)
            with open(path) as f:
                data = json.load(f)
            assert data["url"] == "https://example.com"
        finally:
            os.unlink(path)


class TestPDFReport:
    def test_pdf_fallback_to_html(self, sample_result):
        """Without weasyprint, should fall back to .pdf.html."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            result_path = save_pdf_report(sample_result, path)
            # Should either be .pdf or .pdf.html depending on weasyprint availability
            assert os.path.exists(result_path)
            with open(result_path) as f:
                content = f.read()
            assert "example.com" in content
        finally:
            if os.path.exists(path):
                os.unlink(path)
            fallback = path.replace(".pdf", ".pdf.html")
            if os.path.exists(fallback):
                os.unlink(fallback)
