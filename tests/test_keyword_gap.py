"""Tests for keyword gap analyzer."""
import pytest
from audit.checks.keyword_gap import (
    extract_keywords,
    extract_bigrams,
    analyze_keyword_gap,
    check_keyword_gap
)


def test_extract_keywords():
    """Test keyword extraction."""
    html = """
    <html>
        <body>
            <p>SEO optimization is important for website ranking. 
               SEO tools help improve optimization.</p>
        </body>
    </html>
    """
    keywords = extract_keywords(html)
    
    assert 'seo' in keywords
    assert 'optimization' in keywords
    assert keywords['seo'] == 2
    assert keywords['optimization'] == 2


def test_extract_keywords_filters_stopwords():
    """Test that stop words are filtered."""
    html = "<p>The quick brown fox jumps over the lazy dog</p>"
    keywords = extract_keywords(html)
    
    assert 'the' not in keywords
    assert 'quick' in keywords
    assert 'brown' in keywords


def test_extract_bigrams():
    """Test bigram extraction."""
    html = "<p>search engine optimization is important for search engine ranking</p>"
    bigrams = extract_bigrams(html)
    
    assert 'search engine' in bigrams
    assert bigrams['search engine'] == 2


def test_analyze_keyword_gap():
    """Test keyword gap analysis."""
    your_html = "<p>web design services for small business</p>"
    competitor_html = "<p>web design services for enterprise business and large corporations</p>"
    
    result = analyze_keyword_gap(your_html, [competitor_html], top_n=5)
    
    assert 'keyword_gaps' in result
    assert 'phrase_gaps' in result
    assert 'metrics' in result
    assert 'recommendations' in result
    
    # Should find 'enterprise' and 'large' as gaps
    gap_keywords = [item['keyword'] for item in result['keyword_gaps']]
    assert 'enterprise' in gap_keywords or 'large' in gap_keywords


def test_analyze_keyword_gap_metrics():
    """Test gap analysis metrics calculation."""
    your_html = "<p>python programming tutorial</p>"
    competitor_html = "<p>python programming tutorial advanced course</p>"
    
    result = analyze_keyword_gap(your_html, [competitor_html])
    
    metrics = result['metrics']
    assert 'coverage_rate' in metrics
    assert 'gap_count' in metrics
    assert metrics['coverage_rate'] >= 0
    assert metrics['coverage_rate'] <= 100


def test_check_keyword_gap():
    """Test main check function."""
    html = """
    <html>
        <body>
            <main>
                <h1>SEO Services</h1>
                <p>Professional SEO optimization for your website. 
                   Our SEO experts provide comprehensive SEO audits.</p>
            </main>
        </body>
    </html>
    """
    
    result = check_keyword_gap(html, "https://example.com")
    
    assert 'issues' in result
    assert 'keyword_stats' in result
    assert 'top_keywords' in result['keyword_stats']
    
    # Should find 'seo' as top keyword
    top_kw = result['keyword_stats']['top_keywords'][0]['keyword']
    assert top_kw == 'seo'


def test_check_keyword_gap_no_main_content():
    """Test handling of pages without main content."""
    html = "<html><body><div>Some text</div></body></html>"
    
    result = check_keyword_gap(html, "https://example.com")
    
    # Should still work with body fallback
    assert 'keyword_stats' in result or len(result['issues']) > 0


def test_check_keyword_gap_empty_content():
    """Test handling of empty content."""
    html = "<html><body><main></main></body></html>"
    
    result = check_keyword_gap(html, "https://example.com")
    
    # Should report error for no keywords
    assert any('No keywords found' in issue['message'] for issue in result['issues'])


def test_keyword_diversity_warning():
    """Test low diversity warning."""
    # Repetitive content
    html = """
    <main>
        <p>buy buy buy buy buy buy buy buy buy buy
           cheap cheap cheap cheap cheap cheap</p>
    </main>
    """
    
    result = check_keyword_gap(html, "https://example.com")
    
    # Should warn about low diversity
    assert any('diversity' in issue['message'].lower() for issue in result['issues'])


def test_analyze_keyword_gap_multiple_competitors():
    """Test gap analysis with multiple competitors."""
    your_html = "<p>basic web hosting</p>"
    comp1 = "<p>premium web hosting with ssl certificates</p>"
    comp2 = "<p>enterprise web hosting with dedicated servers</p>"
    
    result = analyze_keyword_gap(your_html, [comp1, comp2], top_n=10)
    
    gap_keywords = [item['keyword'] for item in result['keyword_gaps']]
    
    # Should find keywords from both competitors
    assert 'premium' in gap_keywords or 'enterprise' in gap_keywords
    assert 'ssl' in gap_keywords or 'dedicated' in gap_keywords


def test_recommendations_generation():
    """Test that recommendations are generated."""
    your_html = "<p>simple text</p>"
    competitor_html = "<p>advanced comprehensive detailed extensive thorough complete text</p>"
    
    result = analyze_keyword_gap(your_html, [competitor_html])
    
    assert len(result['recommendations']) > 0
    assert any('keyword' in rec.lower() for rec in result['recommendations'])
