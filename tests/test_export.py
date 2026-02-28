"""Tests for audit.reports.export - CSV/JSON/summary export."""

import json
import pytest
from audit.core import AuditResult
from audit.reports.export import AuditExporter


@pytest.fixture
def sample_results():
    results = []
    for i in range(5):
        r = AuditResult(url=f"https://site{i}.com", domain=f"site{i}.com")
        r.score = 50 + i * 10
        r.load_time = 1.0 + i * 0.5
        r.status_code = 200
        r.title = f"Site {i} Title"
        r.meta_description = f"Description for site {i}"
        r.timestamp = "2026-02-28T18:00:00+00:00"
        r.add_issue("error", "meta", f"Error {i}", 5)
        r.add_issue("warning", "links", f"Warning {i}", 2)
        r.add_pass("security", f"Pass {i}")
        results.append(r)
    return results


class TestExportJSON:
    def test_json_valid(self, sample_results):
        output = AuditExporter.to_json(sample_results)
        data = json.loads(output)
        assert len(data) == 5

    def test_json_has_fields(self, sample_results):
        output = AuditExporter.to_json(sample_results)
        data = json.loads(output)
        assert "url" in data[0]
        assert "score" in data[0]
        assert "grade" in data[0]
        assert "error_count" in data[0]

    def test_json_indent(self, sample_results):
        output = AuditExporter.to_json(sample_results, indent=4)
        assert "    " in output


class TestExportCSV:
    def test_csv_has_header(self, sample_results):
        output = AuditExporter.to_csv(sample_results)
        lines = output.strip().split("\n")
        assert "URL" in lines[0]
        assert "Score" in lines[0]
        assert "Grade" in lines[0]

    def test_csv_row_count(self, sample_results):
        output = AuditExporter.to_csv(sample_results)
        lines = output.strip().split("\n")
        assert len(lines) == 6  # header + 5 results

    def test_csv_contains_urls(self, sample_results):
        output = AuditExporter.to_csv(sample_results)
        assert "site0.com" in output
        assert "site4.com" in output


class TestExportJSONL:
    def test_jsonl_line_count(self, sample_results):
        output = AuditExporter.to_jsonl(sample_results)
        lines = output.strip().split("\n")
        assert len(lines) == 5

    def test_jsonl_each_line_valid(self, sample_results):
        output = AuditExporter.to_jsonl(sample_results)
        for line in output.strip().split("\n"):
            data = json.loads(line)
            assert "url" in data


class TestExportSummary:
    def test_summary_has_stats(self, sample_results):
        output = AuditExporter.to_summary(sample_results)
        assert "URLs audited: 5" in output
        assert "Average score:" in output
        assert "Total errors:" in output

    def test_summary_has_grades(self, sample_results):
        output = AuditExporter.to_summary(sample_results)
        assert "Grade Distribution:" in output

    def test_summary_has_top_issues(self, sample_results):
        output = AuditExporter.to_summary(sample_results)
        assert "Top Issues:" in output

    def test_summary_has_worst_performers(self, sample_results):
        output = AuditExporter.to_summary(sample_results)
        assert "Worst Performers:" in output

    def test_summary_empty_results(self):
        output = AuditExporter.to_summary([])
        assert "No results" in output


class TestSaveExport:
    def test_save_to_file(self, sample_results, tmp_path):
        filepath = str(tmp_path / "test_export.json")
        content = AuditExporter.to_json(sample_results)
        result = AuditExporter.save(content, filepath)
        assert result == filepath
        with open(filepath) as f:
            data = json.loads(f.read())
        assert len(data) == 5

    def test_save_csv(self, sample_results, tmp_path):
        filepath = str(tmp_path / "test_export.csv")
        content = AuditExporter.to_csv(sample_results)
        AuditExporter.save(content, filepath)
        with open(filepath) as f:
            lines = f.readlines()
        assert len(lines) == 6
