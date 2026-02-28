"""Tests for audit.checks.links - internal/external links, images, nofollow."""

import pytest
from unittest.mock import MagicMock
from audit.core import AuditResult, HTMLAnalyzer
from audit.checks.links import LinksCheck


@pytest.fixture
def check():
    return LinksCheck()


def _run(check, result, html, domain="example.com"):
    analyzer = HTMLAnalyzer()
    analyzer.set_domain(domain)
    analyzer.feed(html)
    resp = MagicMock()
    resp.status_code = 200
    resp.text = html
    resp.content = html.encode()
    resp.headers = {}
    check.run(result, resp, analyzer)
    return result


class TestLinksCheck:
    def test_internal_links_detected(self, check, result_template, perfect_html):
        r = _run(check, result_template, perfect_html)
        assert r.details.get("internal_links", 0) >= 2

    def test_external_links_detected(self, check, result_template, perfect_html):
        r = _run(check, result_template, perfect_html)
        assert r.details.get("external_links", 0) >= 1

    def test_no_internal_links_warning(self, check, result_template):
        html = '<html><body><a href="https://other.com">ext</a></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("内部链接" in w or "internal" in w.lower() for w in warnings)

    def test_too_many_external_links(self, check, result_template):
        links = ''.join(f'<a href="https://ext{i}.com">link</a>' for i in range(110))
        html = f'<html><body><a href="/int">int</a>{links}</body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("外部链接过多" in w for w in warnings)

    def test_images_all_have_alt(self, check, result_template):
        html = '<html><body><img src="a.jpg" alt="A"><img src="b.jpg" alt="B"></body></html>'
        r = _run(check, result_template, html)
        passed = [i.message for i in r.passed]
        assert any("alt" in p for p in passed)

    def test_images_missing_alt(self, check, result_template):
        html = '<html><body><img src="a.jpg"><img src="b.jpg" alt="B"></body></html>'
        r = _run(check, result_template, html)
        errors = [i.message for i in r.errors]
        assert any("alt" in e for e in errors)

    def test_images_empty_alt(self, check, result_template):
        html = '<html><body><img src="a.jpg" alt=""><img src="b.jpg" alt=""></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("alt为空" in w for w in warnings)

    def test_no_lazy_loading_warning(self, check, result_template):
        imgs = ''.join(f'<img src="{i}.jpg" alt="img{i}">' for i in range(5))
        html = f'<html><body>{imgs}</body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("lazy" in w.lower() for w in warnings)

    def test_lazy_loading_pass(self, check, result_template):
        html = '<html><body><img src="a.jpg" alt="A" loading="lazy" width="100" height="100"></body></html>'
        r = _run(check, result_template, html)
        passed = [i.message for i in r.passed]
        assert any("lazy" in p.lower() for p in passed)

    def test_no_images(self, check, result_template):
        html = '<html><body><p>No images</p></body></html>'
        r = _run(check, result_template, html)
        info = [i for i in r.issues if i.severity == "info"]
        assert any("图片" in i.message or "image" in i.message.lower() for i in info)

    def test_images_missing_dimensions(self, check, result_template):
        html = '<html><body><img src="a.jpg" alt="A"><img src="b.jpg" alt="B"></body></html>'
        r = _run(check, result_template, html)
        warnings = [i.message for i in r.warnings]
        assert any("宽高" in w or "CLS" in w for w in warnings)
