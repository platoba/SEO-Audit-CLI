"""Tests for audit.checks.accessibility - WCAG 2.1 heuristic checks."""

import pytest
from unittest.mock import MagicMock
from audit.core import AuditResult, HTMLAnalyzer
from audit.checks.accessibility import AccessibilityCheck


@pytest.fixture
def check():
    return AccessibilityCheck()


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


class TestAccessibilityCheck:
    def test_perfect_page_no_errors(self, check, result_template, perfect_html):
        r = _run(check, result_template, perfect_html)
        errors = [i for i in r.issues if i.severity == "error"]
        assert len(errors) == 0, [e.message for e in errors]

    def test_missing_lang_error(self, check, result_template):
        html = '<html><head><title>T</title></head><body><main><h1>H</h1></main></body></html>'
        r = _run(check, result_template, html)
        errors = [i.message for i in r.errors]
        assert any("lang" in e.lower() or "语言" in e for e in errors)

    def test_missing_alt_error(self, check, result_template):
        html = '<!DOCTYPE html><html lang="en"><body><main><h1>H</h1><nav>N</nav><img src="x.jpg"></main></body></html>'
        r = _run(check, result_template, html)
        errors = [i.message for i in r.errors]
        assert any("alt" in e for e in errors)

    def test_missing_main_landmark(self, check, result_template):
        html = '<!DOCTYPE html><html lang="en"><body><div><h1>H</h1></div></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("main" in w.lower() or "地标" in w for w in warnings)

    def test_skip_link_detected(self, check, result_template, perfect_html):
        r = _run(check, result_template, perfect_html)
        passed = [i.message for i in r.passed]
        assert any("skip" in p.lower() or "跳转" in p for p in passed)

    def test_missing_skip_link(self, check, result_template):
        html = '<!DOCTYPE html><html lang="en"><body><main><h1>H</h1><nav>N</nav></main></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("skip" in w.lower() or "跳转" in w for w in warnings)

    def test_heading_order_ok(self, check, result_template):
        html = '<!DOCTYPE html><html lang="en"><body><main><h1>A</h1><h2>B</h2><h3>C</h3><nav>N</nav></main></body></html>'
        r = _run(check, result_template, html)
        passed = [i.message for i in r.passed]
        assert any("标题层级" in p or "heading" in p.lower() for p in passed)

    def test_heading_order_skip(self, check, result_template):
        html = '<!DOCTYPE html><html lang="en"><body><main><h1>A</h1><h3>C</h3><nav>N</nav></main></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("层级跳跃" in w or "H1" in w for w in warnings)

    def test_no_headings_warning(self, check, result_template):
        html = '<!DOCTYPE html><html lang="en"><body><main><p>text</p><nav>N</nav></main></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("标题" in w or "heading" in w.lower() for w in warnings)

    def test_doctype_pass(self, check, result_template):
        html = '<!DOCTYPE html><html lang="en"><body><main><h1>H</h1><nav>N</nav></main></body></html>'
        r = _run(check, result_template, html)
        passed = [i.message for i in r.passed]
        assert any("DOCTYPE" in p for p in passed)

    def test_no_doctype_warning(self, check, result_template):
        html = '<html lang="en"><body><main><h1>H</h1><nav>N</nav></main></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("DOCTYPE" in w for w in warnings)

    def test_form_labels(self, check, result_template):
        html = '<!DOCTYPE html><html lang="en"><body><main><h1>H</h1><nav>N</nav><form><label for="e">Email</label><input id="e"></form></main></body></html>'
        r = _run(check, result_template, html)
        passed = [i.message for i in r.passed]
        assert any("label" in p.lower() for p in passed)

    def test_low_contrast_hint(self, check, result_template):
        html = '<!DOCTYPE html><html lang="en"><body><main><h1>H</h1><nav>N</nav><p style="color:#eeeeee">Light text</p></main></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("对比度" in w or "contrast" in w.lower() for w in warnings)

    def test_bad_tabindex(self, check, result_template):
        html = '<!DOCTYPE html><html lang="en"><body><main><h1>H</h1><nav>N</nav><button tabindex="5">Click</button></main></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("tabindex" in w for w in warnings)
