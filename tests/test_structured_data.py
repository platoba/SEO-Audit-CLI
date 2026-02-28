"""Tests for audit.checks.structured_data - JSON-LD, Microdata, RDFa."""

import pytest
from unittest.mock import MagicMock
from audit.core import AuditResult, HTMLAnalyzer
from audit.checks.structured_data import StructuredDataCheck


@pytest.fixture
def check():
    return StructuredDataCheck()


def _run(check, result, html):
    analyzer = HTMLAnalyzer()
    analyzer.set_domain("example.com")
    analyzer.feed(html)
    resp = MagicMock()
    resp.status_code = 200
    resp.text = html
    resp.content = html.encode()
    resp.headers = {}
    check.run(result, resp, analyzer)
    return result


class TestStructuredDataCheck:
    def test_json_ld_detected(self, check, result_template, perfect_html):
        r = _run(check, result_template, perfect_html)
        assert len(r.details.get("json_ld_types", [])) >= 1
        passed = [i.message for i in r.passed]
        assert any("结构化数据" in p or "JSON-LD" in p for p in passed)

    def test_no_structured_data_warning(self, check, result_template):
        html = '<html><body><p>Plain</p></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("结构化数据" in w for w in warnings)

    def test_invalid_json_ld(self, check, result_template):
        html = '<html><head><script type="application/ld+json">{invalid json!!}</script></head><body></body></html>'
        r = _run(check, result_template, html)
        errors = [i.message for i in r.errors]
        assert any("JSON-LD" in e or "解析" in e for e in errors)

    def test_organization_schema(self, check, result_template):
        html = '''<html><head><script type="application/ld+json">
        {"@context":"https://schema.org","@type":"Organization","name":"Acme","url":"https://acme.com"}
        </script></head><body></body></html>'''
        r = _run(check, result_template, html)
        assert "Organization" in r.details.get("json_ld_types", [])

    def test_organization_missing_name(self, check, result_template):
        html = '''<html><head><script type="application/ld+json">
        {"@context":"https://schema.org","@type":"Organization","url":"https://acme.com"}
        </script></head><body></body></html>'''
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("name" in w for w in warnings)

    def test_article_missing_fields(self, check, result_template):
        html = '''<html><head><script type="application/ld+json">
        {"@context":"https://schema.org","@type":"Article","headline":"Title"}
        </script></head><body></body></html>'''
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("author" in w or "datePublished" in w for w in warnings)

    def test_product_schema(self, check, result_template):
        html = '''<html><head><script type="application/ld+json">
        {"@context":"https://schema.org","@type":"Product","name":"Widget","offers":{"price":"9.99"}}
        </script></head><body></body></html>'''
        r = _run(check, result_template, html)
        assert "Product" in r.details.get("json_ld_types", [])

    def test_microdata_detected(self, check, result_template):
        html = '<html><body><div itemscope itemtype="https://schema.org/Organization"><span itemprop="name">Acme</span></div></body></html>'
        r = _run(check, result_template, html)
        assert len(r.details.get("microdata_types", [])) >= 1

    def test_rdfa_detected(self, check, result_template):
        html = '<html><body><div vocab="https://schema.org/" typeof="Organization"><span property="name">Acme</span></div></body></html>'
        r = _run(check, result_template, html)
        assert r.details.get("has_rdfa") is True

    def test_missing_context_warning(self, check, result_template):
        html = '''<html><head><script type="application/ld+json">
        {"@type":"Organization","name":"Acme"}
        </script></head><body></body></html>'''
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("@context" in w for w in warnings)

    def test_breadcrumb_missing_items(self, check, result_template):
        html = '''<html><head><script type="application/ld+json">
        {"@context":"https://schema.org","@type":"BreadcrumbList"}
        </script></head><body></body></html>'''
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("BreadcrumbList" in w for w in warnings)
