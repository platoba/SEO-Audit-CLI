"""Tests for audit.checks.keyword - keyword density analysis."""

import pytest
from unittest.mock import MagicMock
from audit.core import AuditResult, HTMLAnalyzer
from audit.checks.keyword import KeywordCheck, KeywordAnalyzer


@pytest.fixture
def check():
    return KeywordCheck()


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


class TestKeywordAnalyzer:
    def test_basic_analysis(self):
        ka = KeywordAnalyzer("The quick brown fox jumps over the lazy dog")
        assert ka.total_words > 0
        assert ka.unique_words > 0

    def test_stop_words_filtered(self):
        ka = KeywordAnalyzer("the the the and and or but is are")
        assert ka.total_words == 0  # all stop words

    def test_word_frequency(self):
        ka = KeywordAnalyzer("python python python java java ruby")
        top = ka.top_keywords(3)
        assert top[0][0] == "python"
        assert top[0][1] == 3

    def test_bigrams(self):
        ka = KeywordAnalyzer("machine learning machine learning deep learning")
        bigrams = ka.top_bigrams(3)
        phrases = [b[0] for b in bigrams]
        assert "machine learning" in phrases

    def test_trigrams(self):
        ka = KeywordAnalyzer("natural language processing natural language processing NLP")
        trigrams = ka.top_trigrams(3)
        assert len(trigrams) > 0

    def test_lexical_diversity(self):
        # All unique words
        ka = KeywordAnalyzer("python java ruby golang rust swift")
        assert ka.lexical_diversity == 1.0

        # Repeated words
        ka2 = KeywordAnalyzer("python python python python")
        assert ka2.lexical_diversity < 0.5

    def test_density_of(self):
        ka = KeywordAnalyzer("seo seo seo audit audit tool")
        d = ka.density_of("seo")
        assert d > 0

    def test_keyword_in_title(self):
        ka = KeywordAnalyzer("content", title="SEO Audit Tool")
        assert ka.keyword_in_title("seo") is True
        assert ka.keyword_in_title("python") is False

    def test_keyword_in_meta(self):
        ka = KeywordAnalyzer("content", meta_desc="Best SEO tool for auditing")
        assert ka.keyword_in_meta("seo") is True
        assert ka.keyword_in_meta("java") is False

    def test_empty_text(self):
        ka = KeywordAnalyzer("")
        assert ka.total_words == 0
        assert ka.lexical_diversity == 0

    def test_html_stripped(self):
        ka = KeywordAnalyzer("<p>hello</p> <div>world</div>")
        assert "hello" in [w for w, _, _ in ka.top_keywords()]


class TestKeywordCheck:
    def test_thin_content_warning(self, check):
        html = "<html><head><title>Test</title></head><body><p>Short page.</p></body></html>"
        result = _run(check, html)
        warnings = [i.message for i in result.warnings]
        assert any("过少" in w for w in warnings)

    def test_rich_content_pass(self, check):
        words = " ".join(f"word{i}" for i in range(500))
        html = f"<html><head><title>Test</title></head><body><p>{words}</p></body></html>"
        result = _run(check, html)
        passed = [i.message for i in result.passed]
        assert any("丰富" in p or "OK" in p for p in passed)

    def test_keyword_stuffing_detection(self, check):
        # Repeat one keyword excessively
        stuffed = " ".join(["seotools"] * 50 + [f"word{i}" for i in range(100)])
        html = f"<html><head><title>Test</title></head><body><p>{stuffed}</p></body></html>"
        result = _run(check, html)
        warnings = [i.message for i in result.warnings]
        assert any("密度过高" in w or "过度优化" in w for w in warnings)

    def test_keyword_details_present(self, check):
        words = " ".join(f"keyword{i % 20}" for i in range(400))
        html = f"<html><head><title>Test</title></head><body><p>{words}</p></body></html>"
        result = _run(check, html)
        kw = result.details.get("keywords", {})
        assert "total_words" in kw
        assert "top_keywords" in kw
        assert "top_bigrams" in kw

    def test_title_keyword_alignment(self, check):
        words = " ".join(["python"] * 30 + [f"word{i}" for i in range(300)])
        html = f"<html><head><title>Python Tutorial</title><meta name='description' content='Learn Python'></head><body><p>{words}</p></body></html>"
        result = _run(check, html)
        passed = [i.message for i in result.passed]
        assert any("标题" in p for p in passed)

    def test_normal_density_pass(self, check):
        # Normal distribution - no keyword appears too much
        words = " ".join(f"unique{i}" for i in range(400))
        html = f"<html><head><title>Test</title></head><body><p>{words}</p></body></html>"
        result = _run(check, html)
        passed = [i.message for i in result.passed]
        assert any("密度正常" in p for p in passed)
