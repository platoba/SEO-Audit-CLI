"""
Competitor Keyword Gap Analyzer
Identifies keywords competitors rank for but your site doesn't.
"""
import re
from collections import Counter
from typing import Dict, List, Set, Tuple
from bs4 import BeautifulSoup


def extract_keywords(html: str, min_length: int = 3) -> Counter:
    """Extract keywords from HTML content."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style elements
    for script in soup(['script', 'style', 'noscript']):
        script.decompose()
    
    # Get text
    text = soup.get_text(separator=' ', strip=True)
    
    # Tokenize and clean
    words = re.findall(r'\b[a-z]{' + str(min_length) + r',}\b', text.lower())
    
    # Filter common stop words
    stop_words = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her',
        'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how',
        'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did',
        'its', 'let', 'put', 'say', 'she', 'too', 'use', 'with', 'this', 'that',
        'from', 'have', 'they', 'will', 'what', 'been', 'more', 'when', 'your',
        'about', 'after', 'could', 'other', 'their', 'there', 'these', 'which',
        'would', 'because', 'through', 'should'
    }
    
    filtered = [w for w in words if w not in stop_words]
    return Counter(filtered)


def extract_bigrams(html: str) -> Counter:
    """Extract 2-word phrases."""
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup(['script', 'style', 'noscript']):
        script.decompose()
    
    text = soup.get_text(separator=' ', strip=True)
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
    return Counter(bigrams)


def analyze_keyword_gap(
    your_html: str,
    competitor_htmls: List[str],
    top_n: int = 20
) -> Dict:
    """
    Analyze keyword gaps between your site and competitors.
    
    Args:
        your_html: HTML content of your site
        competitor_htmls: List of competitor HTML contents
        top_n: Number of top gap keywords to return
    
    Returns:
        Dict with gap analysis results
    """
    # Extract keywords from your site
    your_keywords = extract_keywords(your_html)
    your_bigrams = extract_bigrams(your_html)
    
    # Extract keywords from competitors
    competitor_keywords = Counter()
    competitor_bigrams = Counter()
    
    for comp_html in competitor_htmls:
        competitor_keywords.update(extract_keywords(comp_html))
        competitor_bigrams.update(extract_bigrams(comp_html))
    
    # Find gaps (keywords competitors have but you don't)
    keyword_gaps = {}
    for word, count in competitor_keywords.most_common(100):
        if word not in your_keywords or your_keywords[word] < count * 0.3:
            keyword_gaps[word] = {
                'competitor_count': count,
                'your_count': your_keywords.get(word, 0),
                'gap_score': count - your_keywords.get(word, 0)
            }
    
    bigram_gaps = {}
    for phrase, count in competitor_bigrams.most_common(50):
        if phrase not in your_bigrams or your_bigrams[phrase] < count * 0.3:
            bigram_gaps[phrase] = {
                'competitor_count': count,
                'your_count': your_bigrams.get(phrase, 0),
                'gap_score': count - your_bigrams.get(phrase, 0)
            }
    
    # Sort by gap score
    top_keyword_gaps = sorted(
        keyword_gaps.items(),
        key=lambda x: x[1]['gap_score'],
        reverse=True
    )[:top_n]
    
    top_bigram_gaps = sorted(
        bigram_gaps.items(),
        key=lambda x: x[1]['gap_score'],
        reverse=True
    )[:top_n]
    
    # Calculate coverage metrics
    total_competitor_keywords = len(competitor_keywords)
    your_coverage = len(set(your_keywords.keys()) & set(competitor_keywords.keys()))
    coverage_rate = (your_coverage / total_competitor_keywords * 100) if total_competitor_keywords > 0 else 0
    
    return {
        'keyword_gaps': [
            {
                'keyword': kw,
                'competitor_mentions': data['competitor_count'],
                'your_mentions': data['your_count'],
                'gap_score': data['gap_score']
            }
            for kw, data in top_keyword_gaps
        ],
        'phrase_gaps': [
            {
                'phrase': phrase,
                'competitor_mentions': data['competitor_count'],
                'your_mentions': data['your_count'],
                'gap_score': data['gap_score']
            }
            for phrase, data in top_bigram_gaps
        ],
        'metrics': {
            'total_competitor_keywords': total_competitor_keywords,
            'your_unique_keywords': len(your_keywords),
            'shared_keywords': your_coverage,
            'coverage_rate': round(coverage_rate, 2),
            'gap_count': len(keyword_gaps)
        },
        'recommendations': generate_recommendations(
            top_keyword_gaps,
            top_bigram_gaps,
            coverage_rate
        )
    }


def generate_recommendations(
    keyword_gaps: List[Tuple],
    phrase_gaps: List[Tuple],
    coverage_rate: float
) -> List[str]:
    """Generate actionable recommendations based on gap analysis."""
    recommendations = []
    
    if coverage_rate < 30:
        recommendations.append(
            "🔴 Critical: Your keyword coverage is very low (<30%). "
            "Consider a major content strategy overhaul."
        )
    elif coverage_rate < 60:
        recommendations.append(
            "🟡 Warning: Your keyword coverage is below 60%. "
            "Focus on adding content around missing keywords."
        )
    else:
        recommendations.append(
            "✅ Good: Your keyword coverage is above 60%. "
            "Fine-tune with the specific gaps below."
        )
    
    if keyword_gaps:
        top_5 = [kw for kw, _ in keyword_gaps[:5]]
        recommendations.append(
            f"📝 Priority keywords to target: {', '.join(top_5)}"
        )
    
    if phrase_gaps:
        top_3 = [phrase for phrase, _ in phrase_gaps[:3]]
        recommendations.append(
            f"💬 Priority phrases to include: {', '.join(top_3)}"
        )
    
    recommendations.append(
        "🎯 Action: Create new content or update existing pages to include these keywords naturally."
    )
    
    return recommendations


def check_keyword_gap(html: str, url: str, competitor_urls: List[str] = None) -> Dict:
    """
    Main check function for keyword gap analysis.
    
    Args:
        html: HTML content of the target URL
        url: Target URL
        competitor_urls: List of competitor URLs (optional, for future API integration)
    
    Returns:
        Dict with check results
    """
    issues = []
    
    # For now, we'll do a self-analysis (compare different sections of the same page)
    # In production, this would fetch competitor pages
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract main content vs header/footer
    main_content = soup.find('main') or soup.find('article') or soup.find('body')
    header = soup.find('header')
    
    if not main_content:
        issues.append({
            'severity': 'warning',
            'message': 'Could not identify main content area for keyword analysis'
        })
        return {'issues': issues, 'gap_analysis': None}
    
    # Analyze keyword distribution
    main_keywords = extract_keywords(str(main_content))
    
    if not main_keywords:
        issues.append({
            'severity': 'error',
            'message': 'No keywords found in main content'
        })
    
    # Check keyword diversity
    total_words = sum(main_keywords.values())
    unique_keywords = len(main_keywords)
    
    if total_words > 0:
        diversity_ratio = unique_keywords / total_words
        
        if diversity_ratio < 0.3:
            issues.append({
                'severity': 'warning',
                'message': f'Low keyword diversity ({diversity_ratio:.2%}). Content may be repetitive.'
            })
    
    # Get top keywords
    top_keywords = main_keywords.most_common(10)
    
    return {
        'issues': issues,
        'keyword_stats': {
            'total_words': total_words,
            'unique_keywords': unique_keywords,
            'diversity_ratio': round(diversity_ratio, 3) if total_words > 0 else 0,
            'top_keywords': [
                {'keyword': kw, 'count': count}
                for kw, count in top_keywords
            ]
        },
        'note': 'Full competitor gap analysis requires competitor URLs (future feature)'
    }


# Integration with audit framework
from .base import BaseCheck


class KeywordGapCheck(BaseCheck):
    """Keyword gap analysis check."""
    
    name = "keyword_gap"
    description = "Analyze keyword gaps and content diversity"
    
    def run(self, result, response, analyzer):
        """Run keyword gap check."""
        html = response.text
        url = response.url
        
        gap_result = check_keyword_gap(html, url)
        
        # Add issues to result
        for issue in gap_result.get('issues', []):
            if issue['severity'] == 'error':
                result.add_issue('keyword_gap', issue['message'], 'error')
            else:
                result.add_issue('keyword_gap', issue['message'], 'warning')
        
        # Store keyword stats in result
        if 'keyword_stats' in gap_result:
            result.details['keyword_gap'] = gap_result['keyword_stats']
