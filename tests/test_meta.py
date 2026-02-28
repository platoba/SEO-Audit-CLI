"""Tests for audit.checks.meta - title, description, OG, canonical, headings, lang."""

import pytest
from audit.core import AuditResult, HTMLAnalyzer
from audit.checks.meta import MetaCheck


@pytest.fixture
def check():
    return MetaCheck()


def _run(check, result, html, url="https://example.com"):
    from unittest.mock import MagicMock
    analyzer = HTMLAnalyzer()
    analyzer.set_domain(result.domain)
    analyzer.feed(html)
    resp = MagicMock()
    resp.status_code = 200
    resp.text = html
    resp.content = html.encode()
    resp.headers = {}
    check.run(result, resp, analyzer)
    return result


class TestMetaCheck:
    def test_perfect_page(self, check, result_template, perfect_html):
        r = _run(check, result_template, perfect_html)
        errors = [i for i in r.issues if i.severity == "error"]
        assert len(errors) == 0, [e.message for e in errors]

    def test_missing_title(self, check, result_template):
        html = '<html><head></head><body></body></html>'
        r = _run(check, result_template, html)
        msgs = [i.message for i in r.errors]
        assert any("title" in m.lower() for m in msgs)

    def test_short_title(self, check, result_template):
        html = '<html><head><title>Hi</title></head><body><h1>Hi</h1></body></html>'
        r = _run(check, result_template, html)
        warnings = [i for i in r.issues if i.severity == "warning"]
        assert any("太短" in w.message or "short" in w.message.lower() for w in warnings)

    def test_long_title(self, check, result_template):
        html = f'<html><head><title>{"A" * 70}</title></head><body><h1>H</h1></body></html>'
        r = _run(check, result_template, html)
        warnings = [i for i in r.issues if i.severity == "warning"]
        assert any("太长" in w.message for w in warnings)

    def test_missing_description(self, check, result_template):
        html = '<html lang="en"><head><title>Good Title Here!</title></head><body><h1>H</h1></body></html>'
        r = _run(check, result_template, html)
        msgs = [i.message for i in r.errors]
        assert any("description" in m.lower() for m in msgs)

    def test_short_description(self, check, result_template):
        html = '<html lang="en"><head><title>Good Title Here!</title><meta name="description" content="Short"></head><body><h1>H</h1></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("描述太短" in w for w in warnings)

    def test_missing_h1(self, check, result_template):
        html = '<html lang="en"><head><title>Good Title Here!</title><meta name="description" content="' + 'x' * 120 + '"></head><body><h2>Sub</h2></body></html>'
        r = _run(check, result_template, html)
        msgs = [i.message for i in r.errors]
        assert any("H1" in m for m in msgs)

    def test_multiple_h1(self, check, result_template):
        html = '<html lang="en"><head><title>Good Title Here!</title><meta name="description" content="' + 'x' * 120 + '"></head><body><h1>A</h1><h1>B</h1></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("多个H1" in w for w in warnings)

    def test_missing_og_tags(self, check, result_template):
        html = '<html lang="en"><head><title>Good Title Here!</title><meta name="description" content="' + 'x' * 120 + '"></head><body><h1>H</h1></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("og" in w.lower() or "Open Graph" in w for w in warnings)

    def test_missing_canonical(self, check, result_template):
        html = '<html lang="en"><head><title>Good Title Here!</title><meta name="description" content="' + 'x' * 120 + '"></head><body><h1>H</h1></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("canonical" in w.lower() for w in warnings)

    def test_missing_lang(self, check, result_template):
        html = '<html><head><title>Good Title Here!</title><meta name="description" content="' + 'x' * 120 + '"></head><body><h1>H</h1></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("lang" in w.lower() for w in warnings)

    def test_heading_hierarchy_skip(self, check, result_template):
        html = '<html lang="en"><head><title>Good Title Here!</title><meta name="description" content="' + 'x' * 120 + '"></head><body><h1>H</h1><h3>Skip</h3></body></html>'
        r = _run(check, result_template, html)
        all_msgs = [i.message for i in r.issues]
        assert any("层级跳跃" in m for m in all_msgs)

    def test_noindex_robots(self, check, result_template):
        html = '<html lang="en"><head><title>Good Title Here!</title><meta name="description" content="' + 'x' * 120 + '"><meta name="robots" content="noindex, nofollow"></head><body><h1>H</h1></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("noindex" in w.lower() for w in warnings)
