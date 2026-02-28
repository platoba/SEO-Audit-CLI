"""Batch audit - sitemap import and bulk scanning."""

import re
import requests
from typing import List, Optional
from urllib.parse import urlparse
from xml.etree import ElementTree

from .core import AuditEngine, AuditResult


def parse_sitemap(sitemap_url: str, timeout: int = 10) -> List[str]:
    """Parse sitemap.xml and return list of URLs."""
    headers = {"User-Agent": "SEO-Audit-CLI/2.0"}
    response = requests.get(sitemap_url, timeout=timeout, headers=headers)
    response.raise_for_status()

    urls = []
    content = response.text

    # Handle sitemap index
    if "<sitemapindex" in content:
        urls.extend(_parse_sitemap_index(content, timeout))
    else:
        urls.extend(_parse_sitemap_urls(content))

    return urls


def _parse_sitemap_index(content: str, timeout: int) -> List[str]:
    """Parse sitemap index and fetch child sitemaps."""
    urls = []
    try:
        root = ElementTree.fromstring(content)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for sitemap in root.findall(".//sm:sitemap/sm:loc", ns):
            if sitemap.text:
                child_urls = parse_sitemap(sitemap.text.strip(), timeout)
                urls.extend(child_urls)
        # Fallback: try without namespace
        if not urls:
            for sitemap in root.findall(".//sitemap/loc"):
                if sitemap.text:
                    child_urls = parse_sitemap(sitemap.text.strip(), timeout)
                    urls.extend(child_urls)
    except ElementTree.ParseError:
        pass
    return urls


def _parse_sitemap_urls(content: str) -> List[str]:
    """Parse URLs from a urlset sitemap."""
    urls = []
    try:
        root = ElementTree.fromstring(content)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for url_elem in root.findall(".//sm:url/sm:loc", ns):
            if url_elem.text:
                urls.append(url_elem.text.strip())
        # Fallback without namespace
        if not urls:
            for url_elem in root.findall(".//url/loc"):
                if url_elem.text:
                    urls.append(url_elem.text.strip())
    except ElementTree.ParseError:
        # Try regex fallback
        urls = re.findall(r"<loc>(https?://[^<]+)</loc>", content)
    return urls


def batch_audit(
    urls: List[str],
    max_urls: int = 50,
    engine: Optional[AuditEngine] = None,
    progress_callback=None,
) -> List[AuditResult]:
    """Audit multiple URLs with optional progress callback."""
    if engine is None:
        engine = AuditEngine()

    urls = urls[:max_urls]
    results = []

    for i, url in enumerate(urls):
        try:
            result = engine.audit(url)
            results.append(result)
        except Exception as e:
            # Create a failed result
            r = AuditResult(url=url, domain=urlparse(url).netloc, score=0)
            r.add_issue("error", "batch", f"审计失败: {e}", 50)
            results.append(r)

        if progress_callback:
            progress_callback(i + 1, len(urls), url, results[-1])

    return results


def batch_audit_from_sitemap(
    sitemap_url: str,
    max_urls: int = 50,
    engine: Optional[AuditEngine] = None,
    progress_callback=None,
) -> List[AuditResult]:
    """Parse sitemap and audit all URLs."""
    urls = parse_sitemap(sitemap_url)
    return batch_audit(urls, max_urls=max_urls, engine=engine, progress_callback=progress_callback)
