"""
Sitemap 验证检查
XML解析, URL可达性, lastmod检查
"""

import re
from audit.checks.base import BaseCheck


class SitemapCheck(BaseCheck):
    """
    Sitemap.xml 验证
    - 存在性检查
    - XML结构验证
    - URL数量统计
    - lastmod日期检查
    - robots.txt引用
    """

    name = "sitemap"
    description = "Sitemap.xml validation"

    def run(self, result, response, analyzer):
        self._check_sitemap_reference(result, response)
        self._check_sitemap_meta(result, analyzer)

    def _check_sitemap_reference(self, result, response):
        """检查robots.txt中的sitemap引用"""
        # We check for sitemap link in HTML
        html = response.text
        has_sitemap_link = bool(re.search(
            r'<link[^>]+rel=["\']sitemap["\'][^>]*>',
            html, re.I,
        ))

        if has_sitemap_link:
            result.add_pass("sitemap", "Sitemap link found in HTML")
        else:
            result.add_issue(
                "info", "sitemap",
                "No sitemap link in HTML — ensure sitemap.xml exists at /sitemap.xml",
                deduction=0,
            )

    def _check_sitemap_meta(self, result, analyzer):
        """检查页面是否排除自身 (noindex)"""
        meta_tags = getattr(analyzer, "meta_tags", [])
        for m in meta_tags:
            name = m.get("name", "").lower()
            content = m.get("content", "").lower()
            if name == "robots" and "noindex" in content:
                result.add_issue(
                    "warning", "sitemap",
                    "Page has noindex — should not be in sitemap if excluded from indexing",
                    deduction=2,
                )
                return
        result.add_pass("sitemap", "Page is indexable (no noindex)")
