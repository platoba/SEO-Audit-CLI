"""
Core Web Vitals 检查模块
估算 LCP / FID / CLS 指标
"""

import re
from audit.checks.base import BaseCheck


class CoreWebVitalsCheck(BaseCheck):
    """
    Core Web Vitals 检查
    基于HTML静态分析估算:
    - LCP: 基于最大图片/文本块
    - FID: 基于JS脚本数量和大小
    - CLS: 基于无尺寸图片/iframe
    """

    name = "core_web_vitals"
    description = "Core Web Vitals (LCP/FID/CLS) estimation"

    def run(self, result, response, analyzer):
        self._check_lcp(result, analyzer)
        self._check_fid(result, response, analyzer)
        self._check_cls(result, analyzer)

    def _check_lcp(self, result, analyzer):
        """LCP - Largest Contentful Paint 估算"""
        images = analyzer.images if hasattr(analyzer, 'images') else []
        large_images = [
            img for img in images
            if not img.get("loading") == "lazy"
            and img.get("width", 0) and int(img.get("width", 0)) > 400
        ]

        # Check for preload hints
        has_preload = any(
            link.get("rel") == "preload" and link.get("as") == "image"
            for link in getattr(analyzer, "links", [])
        )

        if large_images and not has_preload:
            result.add_issue(
                "warning", "cwv",
                f"LCP: {len(large_images)} large image(s) without preload hint — consider <link rel='preload'>",
                deduction=3,
            )
        else:
            result.add_pass("cwv", "LCP: hero images properly configured")

        # Check for render-blocking resources
        scripts = getattr(analyzer, "scripts", [])
        blocking_scripts = [
            s for s in scripts
            if not s.get("async") and not s.get("defer") and s.get("src")
        ]
        if blocking_scripts:
            result.add_issue(
                "warning", "cwv",
                f"LCP: {len(blocking_scripts)} render-blocking script(s) — use async/defer",
                deduction=3,
            )

    def _check_fid(self, result, response, analyzer):
        """FID - First Input Delay 估算"""
        scripts = getattr(analyzer, "scripts", [])
        inline_scripts = [s for s in scripts if not s.get("src")]
        external_scripts = [s for s in scripts if s.get("src")]

        total_scripts = len(scripts)
        if total_scripts > 10:
            result.add_issue(
                "warning", "cwv",
                f"FID: {total_scripts} scripts detected — too many may increase input delay",
                deduction=3,
            )
        elif total_scripts > 5:
            result.add_issue(
                "info", "cwv",
                f"FID: {total_scripts} scripts — moderate count",
                deduction=0,
            )
        else:
            result.add_pass("cwv", f"FID: {total_scripts} scripts — good")

        # Check for long inline scripts
        html = response.text
        inline_pattern = re.findall(r'<script[^>]*>([\s\S]*?)</script>', html)
        long_inline = [s for s in inline_pattern if len(s.strip()) > 2000]
        if long_inline:
            result.add_issue(
                "warning", "cwv",
                f"FID: {len(long_inline)} large inline script(s) (>2KB) — extract to external files",
                deduction=2,
            )

    def _check_cls(self, result, analyzer):
        """CLS - Cumulative Layout Shift 估算"""
        images = analyzer.images if hasattr(analyzer, 'images') else []
        no_dimensions = [
            img for img in images
            if not (img.get("width") and img.get("height"))
        ]

        if no_dimensions:
            result.add_issue(
                "error", "cwv",
                f"CLS: {len(no_dimensions)} image(s) without width/height — causes layout shift",
                deduction=5,
            )
        else:
            result.add_pass("cwv", "CLS: all images have explicit dimensions")

        # Check for iframes without dimensions
        iframes = getattr(analyzer, "iframes", [])
        no_dim_iframes = [
            f for f in iframes
            if not (f.get("width") and f.get("height"))
        ]
        if no_dim_iframes:
            result.add_issue(
                "warning", "cwv",
                f"CLS: {len(no_dim_iframes)} iframe(s) without dimensions",
                deduction=3,
            )

        # Check for font-display
        has_font_display = False
        for link in getattr(analyzer, "links", []):
            if "fonts" in link.get("href", ""):
                if "display=swap" in link.get("href", ""):
                    has_font_display = True
        # This is just advisory, not deducting
