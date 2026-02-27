#!/usr/bin/env python3
"""
SEO Audit CLI - 网站SEO审计工具
检查: 标题/描述/H标签/图片alt/链接/速度/结构化数据/robots/sitemap
"""

import sys
import re
import json
import time
import argparse
import requests
from urllib.parse import urlparse, urljoin
from html.parser import HTMLParser

VERSION = "1.0.0"


class HTMLAnalyzer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta = {}
        self.headings = {f"h{i}": [] for i in range(1, 7)}
        self.images = []
        self.links = {"internal": [], "external": []}
        self.scripts = 0
        self.styles = 0
        self._in_title = False
        self._base_domain = ""

    def set_domain(self, domain):
        self._base_domain = domain

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = attrs_dict.get("name", attrs_dict.get("property", "")).lower()
            content = attrs_dict.get("content", "")
            if name and content:
                self.meta[name] = content
        elif tag in self.headings:
            self.headings[tag].append("")
        elif tag == "img":
            self.images.append({
                "src": attrs_dict.get("src", ""),
                "alt": attrs_dict.get("alt", ""),
                "loading": attrs_dict.get("loading", ""),
            })
        elif tag == "a":
            href = attrs_dict.get("href", "")
            if href and not href.startswith(("#", "javascript:", "mailto:", "tel:")):
                parsed = urlparse(href)
                if parsed.netloc and self._base_domain not in parsed.netloc:
                    self.links["external"].append(href)
                else:
                    self.links["internal"].append(href)
        elif tag == "script":
            self.scripts += 1
        elif tag == "link" and attrs_dict.get("rel") == "stylesheet":
            self.styles += 1

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        for h in self.headings:
            if self.headings[h] and self.headings[h][-1] == "":
                self.headings[h][-1] = data.strip()

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False


def audit_url(url, verbose=False):
    """完整SEO审计"""
    if not url.startswith("http"):
        url = "https://" + url

    parsed = urlparse(url)
    domain = parsed.netloc
    results = {"url": url, "domain": domain, "score": 100, "issues": [], "warnings": [], "passed": []}

    def issue(msg, deduct=5):
        results["issues"].append(msg)
        results["score"] -= deduct

    def warn(msg):
        results["warnings"].append(msg)
        results["score"] -= 2

    def passed(msg):
        results["passed"].append(msg)

    # 1. 页面请求
    try:
        start = time.time()
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 SEO-Audit-CLI/1.0"})
        load_time = time.time() - start
        results["status_code"] = r.status_code
        results["load_time"] = round(load_time, 2)
        results["content_length"] = len(r.content)

        if r.status_code != 200:
            issue(f"HTTP {r.status_code} (非200)", 10)
        else:
            passed(f"HTTP 200 OK ({load_time:.1f}s)")

        if load_time > 3:
            issue(f"加载时间 {load_time:.1f}s > 3s", 5)
        elif load_time > 1.5:
            warn(f"加载时间 {load_time:.1f}s (建议<1.5s)")
        else:
            passed(f"加载速度良好 ({load_time:.1f}s)")

    except Exception as e:
        results["score"] = 0
        issue(f"无法访问: {e}", 50)
        return results

    html = r.text

    # 2. HTML分析
    analyzer = HTMLAnalyzer()
    analyzer.set_domain(domain)
    try:
        analyzer.feed(html)
    except:
        pass

    # 3. Title
    title = analyzer.title.strip()
    results["title"] = title
    if not title:
        issue("缺少<title>标签", 10)
    elif len(title) < 10:
        warn(f"标题太短 ({len(title)}字符，建议30-60)")
    elif len(title) > 60:
        warn(f"标题太长 ({len(title)}字符，建议30-60)")
    else:
        passed(f"标题长度OK ({len(title)}字符)")

    # 4. Meta Description
    desc = analyzer.meta.get("description", "")
    results["meta_description"] = desc
    if not desc:
        issue("缺少meta description", 8)
    elif len(desc) < 50:
        warn(f"描述太短 ({len(desc)}字符，建议120-155)")
    elif len(desc) > 160:
        warn(f"描述太长 ({len(desc)}字符，建议120-155)")
    else:
        passed(f"描述长度OK ({len(desc)}字符)")

    # 5. Headings
    h1s = analyzer.headings["h1"]
    if not h1s:
        issue("缺少H1标签", 8)
    elif len(h1s) > 1:
        warn(f"多个H1标签 ({len(h1s)}个，建议1个)")
    else:
        passed(f"H1标签OK: {h1s[0][:50]}")

    # 6. Images
    imgs_no_alt = [img for img in analyzer.images if not img["alt"]]
    if imgs_no_alt:
        issue(f"{len(imgs_no_alt)}/{len(analyzer.images)}张图片缺少alt属性", 5)
    elif analyzer.images:
        passed(f"所有{len(analyzer.images)}张图片都有alt属性")

    lazy_imgs = [img for img in analyzer.images if img["loading"] == "lazy"]
    if analyzer.images and not lazy_imgs:
        warn("没有图片使用lazy loading")

    # 7. Links
    results["internal_links"] = len(analyzer.links["internal"])
    results["external_links"] = len(analyzer.links["external"])
    if not analyzer.links["internal"]:
        warn("没有内部链接")

    # 8. HTTPS
    if not url.startswith("https"):
        issue("未使用HTTPS", 10)
    else:
        passed("HTTPS ✓")

    # 9. Canonical
    canonical = analyzer.meta.get("canonical", "")
    if "canonical" in html.lower():
        passed("有canonical标签")
    else:
        warn("缺少canonical标签")

    # 10. Open Graph
    og_title = analyzer.meta.get("og:title", "")
    og_desc = analyzer.meta.get("og:description", "")
    og_image = analyzer.meta.get("og:image", "")
    if og_title and og_image:
        passed("Open Graph标签完整")
    elif not og_title:
        warn("缺少og:title")

    # 11. Robots.txt
    try:
        robots = requests.get(f"https://{domain}/robots.txt", timeout=5)
        if robots.ok:
            passed("robots.txt存在")
            results["robots_txt"] = True
        else:
            warn("robots.txt不存在或不可访问")
            results["robots_txt"] = False
    except:
        warn("无法检查robots.txt")

    # 12. Sitemap
    try:
        sitemap = requests.get(f"https://{domain}/sitemap.xml", timeout=5)
        if sitemap.ok and "xml" in sitemap.text[:200].lower():
            passed("sitemap.xml存在")
            results["sitemap"] = True
        else:
            warn("sitemap.xml不存在")
            results["sitemap"] = False
    except:
        warn("无法检查sitemap.xml")

    # 13. 页面大小
    size_kb = len(r.content) / 1024
    if size_kb > 3000:
        issue(f"页面过大 ({size_kb:.0f}KB，建议<3MB)", 3)
    elif size_kb > 1000:
        warn(f"页面较大 ({size_kb:.0f}KB)")
    else:
        passed(f"页面大小OK ({size_kb:.0f}KB)")

    # 14. Viewport
    if 'viewport' in html.lower():
        passed("有viewport meta标签（移动端友好）")
    else:
        issue("缺少viewport meta标签", 5)

    results["score"] = max(0, min(100, results["score"]))
    return results


def print_report(results, verbose=False):
    score = results["score"]
    grade = "A+" if score >= 95 else "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"
    color = "\033[92m" if score >= 80 else "\033[93m" if score >= 60 else "\033[91m"

    print(f"\n{'='*60}")
    print(f"  SEO Audit Report: {results['url']}")
    print(f"  Score: {color}{score}/100 ({grade})\033[0m")
    print(f"{'='*60}")

    if results.get("title"):
        print(f"\n  📝 Title: {results['title'][:60]}")
    if results.get("meta_description"):
        print(f"  📋 Description: {results['meta_description'][:80]}...")
    if results.get("load_time"):
        print(f"  ⚡ Load time: {results['load_time']}s")
    print(f"  🔗 Links: {results.get('internal_links', 0)} internal, {results.get('external_links', 0)} external")

    if results["issues"]:
        print(f"\n  ❌ Issues ({len(results['issues'])}):")
        for i in results["issues"]:
            print(f"    • {i}")

    if results["warnings"]:
        print(f"\n  ⚠️  Warnings ({len(results['warnings'])}):")
        for w in results["warnings"]:
            print(f"    • {w}")

    if verbose and results["passed"]:
        print(f"\n  ✅ Passed ({len(results['passed'])}):")
        for p in results["passed"]:
            print(f"    • {p}")

    print()


def main():
    parser = argparse.ArgumentParser(description="SEO Audit CLI - Website SEO analyzer")
    parser.add_argument("url", nargs="?", help="URL to audit")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show passed checks too")
    parser.add_argument("-j", "--json", action="store_true", help="Output as JSON")
    parser.add_argument("--version", action="version", version=f"seo-audit {VERSION}")
    args = parser.parse_args()

    if not args.url:
        parser.print_help()
        sys.exit(1)

    results = audit_url(args.url, args.verbose)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print_report(results, args.verbose)


if __name__ == "__main__":
    main()
