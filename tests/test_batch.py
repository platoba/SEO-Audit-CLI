"""Tests for audit.batch - sitemap parsing and batch auditing."""

import pytest
from unittest.mock import patch, MagicMock
from audit.batch import parse_sitemap, batch_audit, batch_audit_from_sitemap, _parse_sitemap_urls
from audit.core import AuditResult, AuditEngine


SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/</loc></url>
  <url><loc>https://example.com/about</loc></url>
  <url><loc>https://example.com/contact</loc></url>
</urlset>"""

SITEMAP_INDEX_XML = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/sitemap1.xml</loc></sitemap>
  <sitemap><loc>https://example.com/sitemap2.xml</loc></sitemap>
</sitemapindex>"""

SITEMAP_NO_NS = """<?xml version="1.0"?>
<urlset>
  <url><loc>https://example.com/page1</loc></url>
  <url><loc>https://example.com/page2</loc></url>
</urlset>"""


class TestParseSitemap:
    @patch("audit.batch.requests.get")
    def test_parse_simple_sitemap(self, mock_get):
        resp = MagicMock()
        resp.text = SITEMAP_XML
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp

        urls = parse_sitemap("https://example.com/sitemap.xml")
        assert len(urls) == 3
        assert "https://example.com/" in urls

    @patch("audit.batch.requests.get")
    def test_parse_sitemap_index(self, mock_get):
        call_count = [0]
        def side_effect(url, **kwargs):
            r = MagicMock()
            r.raise_for_status = MagicMock()
            if call_count[0] == 0:
                r.text = SITEMAP_INDEX_XML
            else:
                r.text = SITEMAP_XML
            call_count[0] += 1
            return r
        mock_get.side_effect = side_effect

        urls = parse_sitemap("https://example.com/sitemap.xml")
        assert len(urls) >= 3

    def test_parse_urls_no_namespace(self):
        urls = _parse_sitemap_urls(SITEMAP_NO_NS)
        assert len(urls) == 2

    def test_parse_urls_regex_fallback(self):
        bad_xml = "<not valid xml but <loc>https://example.com/a</loc> <loc>https://example.com/b</loc>"
        urls = _parse_sitemap_urls(bad_xml)
        assert len(urls) == 2


class TestBatchAudit:
    @patch("audit.core.requests.get")
    def test_batch_audit_multiple(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "<html><head><title>Test</title></head><body></body></html>"
        resp.content = resp.text.encode()
        resp.headers = {}
        mock_get.return_value = resp

        results = batch_audit(
            ["https://a.com", "https://b.com"],
            engine=AuditEngine(checks=[], timeout=5),
        )
        assert len(results) == 2
        assert all(isinstance(r, AuditResult) for r in results)

    @patch("audit.core.requests.get")
    def test_batch_audit_max_urls(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "<html></html>"
        resp.content = resp.text.encode()
        resp.headers = {}
        mock_get.return_value = resp

        urls = [f"https://example{i}.com" for i in range(100)]
        results = batch_audit(urls, max_urls=5, engine=AuditEngine(checks=[], timeout=5))
        assert len(results) == 5

    @patch("audit.core.requests.get")
    def test_batch_audit_handles_failure(self, mock_get):
        mock_get.side_effect = ConnectionError("fail")

        results = batch_audit(
            ["https://fail.com"],
            engine=AuditEngine(checks=[], timeout=5),
        )
        assert len(results) == 1
        assert results[0].score == 0

    @patch("audit.core.requests.get")
    def test_batch_progress_callback(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "<html></html>"
        resp.content = resp.text.encode()
        resp.headers = {}
        mock_get.return_value = resp

        progress = []
        def cb(i, total, url, result):
            progress.append((i, total))

        batch_audit(
            ["https://a.com", "https://b.com"],
            engine=AuditEngine(checks=[], timeout=5),
            progress_callback=cb,
        )
        assert len(progress) == 2
        assert progress[-1] == (2, 2)
