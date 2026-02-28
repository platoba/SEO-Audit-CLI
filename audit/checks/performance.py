"""Performance check - load time, page size, resource count, Core Web Vitals hints."""

from .base import BaseCheck


class PerformanceCheck(BaseCheck):
    name = "performance"
    description = "Load time, page size, resource count, Core Web Vitals"

    def run(self, result, response, analyzer):
        self._check_status(result, response)
        self._check_load_time(result)
        self._check_page_size(result, response)
        self._check_resources(result, analyzer)
        self._check_compression(result, response)
        self._check_caching(result, response)
        self._check_core_web_vitals_hints(result, response, analyzer)

    def _check_status(self, result, response):
        if response.status_code != 200:
            result.add_issue("error", "performance", f"HTTP {response.status_code} (非200)", 10)
        else:
            result.add_pass("performance", f"HTTP 200 OK")

    def _check_load_time(self, result):
        lt = result.load_time
        if lt > 5:
            result.add_issue("error", "performance", f"加载时间 {lt:.1f}s > 5s", 8)
        elif lt > 3:
            result.add_issue("warning", "performance", f"加载时间 {lt:.1f}s > 3s", 5)
        elif lt > 1.5:
            result.add_issue("warning", "performance", f"加载时间 {lt:.1f}s (建议<1.5s)", 2)
        else:
            result.add_pass("performance", f"加载速度良好 ({lt:.1f}s)")

    def _check_page_size(self, result, response):
        size_kb = len(response.content) / 1024
        result.details["page_size_kb"] = round(size_kb, 1)
        if size_kb > 3000:
            result.add_issue("error", "performance", f"页面过大 ({size_kb:.0f}KB，建议<3MB)", 5)
        elif size_kb > 1000:
            result.add_issue("warning", "performance", f"页面较大 ({size_kb:.0f}KB)", 2)
        else:
            result.add_pass("performance", f"页面大小OK ({size_kb:.0f}KB)")

    def _check_resources(self, result, analyzer):
        js_count = len(analyzer.scripts)
        css_count = len(analyzer.stylesheets)
        result.details["resources"] = {"scripts": js_count, "stylesheets": css_count}

        if js_count > 20:
            result.add_issue("warning", "performance", f"JS文件过多 ({js_count}个)", 2)
        if css_count > 10:
            result.add_issue("warning", "performance", f"CSS文件过多 ({css_count}个)", 2)

        # Check for render-blocking scripts
        blocking = [s for s in analyzer.scripts if not s.get("async") and not s.get("defer")]
        if blocking:
            result.add_issue("warning", "performance", f"{len(blocking)}个JS文件可能阻塞渲染 (无async/defer)", 2)

    def _check_compression(self, result, response):
        encoding = response.headers.get("Content-Encoding", "")
        if encoding in ("gzip", "br", "deflate"):
            result.add_pass("performance", f"已启用压缩 ({encoding})")
        else:
            result.add_issue("warning", "performance", "未检测到内容压缩 (gzip/br)", 2)

    def _check_caching(self, result, response):
        cache_control = response.headers.get("Cache-Control", "")
        if cache_control:
            result.add_pass("performance", f"Cache-Control: {cache_control[:60]}")
        else:
            result.add_issue("info", "performance", "未设置Cache-Control头")

    def _check_core_web_vitals_hints(self, result, response, analyzer):
        """Heuristic CWV analysis (server-side, no real browser)."""
        cwv = {}

        # LCP hint: based on page size + load time
        lcp_estimate = result.load_time
        if lcp_estimate <= 2.5:
            cwv["LCP"] = {"status": "good", "estimate": f"{lcp_estimate:.1f}s"}
            result.add_pass("performance", f"LCP估算良好 (~{lcp_estimate:.1f}s, 目标<2.5s)")
        elif lcp_estimate <= 4.0:
            cwv["LCP"] = {"status": "needs_improvement", "estimate": f"{lcp_estimate:.1f}s"}
            result.add_issue("warning", "performance", f"LCP估算需改进 (~{lcp_estimate:.1f}s, 目标<2.5s)", 3)
        else:
            cwv["LCP"] = {"status": "poor", "estimate": f"{lcp_estimate:.1f}s"}
            result.add_issue("error", "performance", f"LCP估算差 (~{lcp_estimate:.1f}s, 目标<2.5s)", 5)

        # CLS hint: images without dimensions
        imgs_no_dim = [i for i in analyzer.images if not i.get("width") or not i.get("height")]
        iframes = len(analyzer.iframes)
        cls_risk = len(imgs_no_dim) + iframes
        if cls_risk == 0:
            cwv["CLS"] = {"status": "good", "risk_elements": 0}
            result.add_pass("performance", "CLS风险低 (图片有尺寸，无iframe)")
        elif cls_risk <= 3:
            cwv["CLS"] = {"status": "needs_improvement", "risk_elements": cls_risk}
            result.add_issue("warning", "performance", f"CLS风险中等 ({cls_risk}个风险元素)", 2)
        else:
            cwv["CLS"] = {"status": "poor", "risk_elements": cls_risk}
            result.add_issue("warning", "performance", f"CLS风险高 ({cls_risk}个风险元素)", 3)

        # FID/INP hint: based on JS count
        js_count = len(analyzer.scripts)
        if js_count <= 5:
            cwv["INP"] = {"status": "good", "scripts": js_count}
        elif js_count <= 15:
            cwv["INP"] = {"status": "needs_improvement", "scripts": js_count}
            result.add_issue("info", "performance", f"INP风险: {js_count}个JS文件可能影响交互响应")
        else:
            cwv["INP"] = {"status": "poor", "scripts": js_count}
            result.add_issue("warning", "performance", f"INP风险高: {js_count}个JS文件", 2)

        result.details["core_web_vitals"] = cwv
