"""Mobile check - viewport, responsive hints, tap targets."""

import requests
from .base import BaseCheck


class MobileCheck(BaseCheck):
    name = "mobile"
    description = "Viewport, responsive design, mobile-friendliness"

    def run(self, result, response, analyzer):
        self._check_viewport(result, analyzer)
        self._check_font_size(result, analyzer)
        self._check_tap_targets(result, analyzer)
        self._check_mobile_resources(result, analyzer)
        self._check_robots_txt(result)
        self._check_sitemap(result)

    def _check_viewport(self, result, analyzer):
        viewport = analyzer.meta.get("viewport", "")
        if viewport:
            result.add_pass("mobile", f"viewport: {viewport}")
            if "width=device-width" not in viewport:
                result.add_issue("warning", "mobile", "viewport缺少width=device-width", 2)
            if "initial-scale" not in viewport:
                result.add_issue("info", "mobile", "viewport缺少initial-scale")
        else:
            result.add_issue("error", "mobile", "缺少viewport meta标签", 5)

    def _check_font_size(self, result, analyzer):
        html = analyzer.html_raw.lower()
        # Heuristic: check for very small font sizes in inline styles
        import re
        small_fonts = re.findall(r'font-size:\s*(\d+)px', html)
        tiny = [int(f) for f in small_fonts if int(f) < 12]
        if tiny:
            result.add_issue("warning", "mobile", f"检测到{len(tiny)}处小于12px的字体", 2)
        else:
            result.add_pass("mobile", "未检测到过小字体")

    def _check_tap_targets(self, result, analyzer):
        # Heuristic based on link count and structure
        total_links = len(analyzer.links.get("internal", [])) + len(analyzer.links.get("external", []))
        if total_links > 200:
            result.add_issue("warning", "mobile", f"链接数量过多 ({total_links})，可能影响移动端点击", 1)

    def _check_mobile_resources(self, result, analyzer):
        # Check for excessive resources on mobile
        total_resources = len(analyzer.scripts) + len(analyzer.stylesheets)
        if total_resources > 30:
            result.add_issue("warning", "mobile", f"资源文件过多 ({total_resources}个)，影响移动端加载", 2)

    def _check_robots_txt(self, result):
        try:
            robots_url = f"https://{result.domain}/robots.txt"
            r = requests.get(robots_url, timeout=5, headers={"User-Agent": "SEO-Audit-CLI/2.0"})
            if r.ok and len(r.text) > 0:
                result.add_pass("mobile", "robots.txt存在")
                result.details["robots_txt"] = True
                # Check for mobile-specific directives
                if "Googlebot-Mobile" in r.text:
                    result.add_issue("info", "mobile", "robots.txt有移动端专用规则")
            else:
                result.add_issue("warning", "mobile", "robots.txt不存在或不可访问", 2)
                result.details["robots_txt"] = False
        except Exception:
            result.add_issue("warning", "mobile", "无法检查robots.txt", 1)

    def _check_sitemap(self, result):
        try:
            sitemap_url = f"https://{result.domain}/sitemap.xml"
            r = requests.get(sitemap_url, timeout=5, headers={"User-Agent": "SEO-Audit-CLI/2.0"})
            if r.ok and "xml" in r.text[:500].lower():
                result.add_pass("mobile", "sitemap.xml存在")
                result.details["sitemap"] = True
            else:
                result.add_issue("warning", "mobile", "sitemap.xml不存在", 2)
                result.details["sitemap"] = False
        except Exception:
            result.add_issue("warning", "mobile", "无法检查sitemap.xml", 1)
