"""Accessibility check - WCAG 2.1 heuristic checks."""

import re
from .base import BaseCheck


class AccessibilityCheck(BaseCheck):
    name = "accessibility"
    description = "WCAG 2.1 heuristic checks (images, forms, landmarks, contrast hints)"

    def run(self, result, response, analyzer):
        self._check_doctype(result, analyzer)
        self._check_lang(result, analyzer)
        self._check_images_a11y(result, analyzer)
        self._check_form_labels(result, analyzer)
        self._check_landmarks(result, analyzer)
        self._check_skip_link(result, analyzer)
        self._check_aria_usage(result, analyzer)
        self._check_heading_order(result, analyzer)
        self._check_link_text(result, analyzer)
        self._check_color_contrast_hints(result, analyzer)
        self._check_focus_management(result, analyzer)

    def _check_doctype(self, result, analyzer):
        if analyzer.has_doctype:
            result.add_pass("accessibility", "HTML DOCTYPE声明存在")
        else:
            result.add_issue("warning", "accessibility", "缺少DOCTYPE声明", 1)

    def _check_lang(self, result, analyzer):
        if analyzer.lang:
            result.add_pass("accessibility", f"[WCAG 3.1.1] 页面语言已声明: {analyzer.lang}")
        else:
            result.add_issue("error", "accessibility", "[WCAG 3.1.1] 缺少页面语言声明 (html lang)", 3)

    def _check_images_a11y(self, result, analyzer):
        images = analyzer.images
        if not images:
            return

        no_alt = [img for img in images if img.get("alt") is None]
        if no_alt:
            result.add_issue("error", "accessibility", f"[WCAG 1.1.1] {len(no_alt)}张图片缺少alt属性", 3)
        else:
            result.add_pass("accessibility", "[WCAG 1.1.1] 所有图片都有alt属性")

    def _check_form_labels(self, result, analyzer):
        forms = analyzer.forms
        if not forms:
            return

        if analyzer.form_labels > 0:
            result.add_pass("accessibility", f"[WCAG 1.3.1] 表单有{analyzer.form_labels}个label标签")
        else:
            result.add_issue("warning", "accessibility", "[WCAG 1.3.1] 表单缺少label标签", 2)

    def _check_landmarks(self, result, analyzer):
        has_main = analyzer.has_main_landmark
        has_nav = analyzer.has_nav_landmark

        if has_main and has_nav:
            result.add_pass("accessibility", "[WCAG 1.3.1] 页面有main和nav地标")
        elif has_main:
            result.add_pass("accessibility", "[WCAG 1.3.1] 页面有main地标")
            result.add_issue("info", "accessibility", "建议添加nav地标")
        elif has_nav:
            result.add_issue("warning", "accessibility", "[WCAG 1.3.1] 页面缺少main地标", 2)
        else:
            result.add_issue("warning", "accessibility", "[WCAG 1.3.1] 页面缺少地标元素 (main/nav)", 2)

    def _check_skip_link(self, result, analyzer):
        if analyzer.has_skip_link:
            result.add_pass("accessibility", "[WCAG 2.4.1] 有跳转链接 (skip link)")
        else:
            result.add_issue("warning", "accessibility", "[WCAG 2.4.1] 缺少跳转链接 (skip to main content)", 1)

    def _check_aria_usage(self, result, analyzer):
        if analyzer.aria_labels > 0 or analyzer.aria_roles > 0:
            result.add_pass("accessibility", f"ARIA使用: {analyzer.aria_labels}个label, {analyzer.aria_roles}个role")
        else:
            result.add_issue("info", "accessibility", "页面未使用ARIA属性")

        result.details["aria"] = {
            "labels": analyzer.aria_labels,
            "roles": analyzer.aria_roles,
        }

    def _check_heading_order(self, result, analyzer):
        """Check that headings follow proper nesting order."""
        levels_used = []
        for i in range(1, 7):
            if analyzer.headings.get(f"h{i}"):
                levels_used.append(i)

        if not levels_used:
            result.add_issue("warning", "accessibility", "[WCAG 1.3.1] 页面没有标题标签", 2)
            return

        # Check for skipped levels
        for idx in range(1, len(levels_used)):
            if levels_used[idx] - levels_used[idx - 1] > 1:
                result.add_issue("warning", "accessibility",
                    f"[WCAG 1.3.1] 标题层级跳跃: H{levels_used[idx-1]} → H{levels_used[idx]}", 1)
                return

        result.add_pass("accessibility", "[WCAG 1.3.1] 标题层级结构正确")

    def _check_link_text(self, result, analyzer):
        """Check for descriptive link text."""
        bad_texts = {"click here", "here", "read more", "more", "link", "点击这里", "更多", "详情"}
        all_links = analyzer.links.get("internal", []) + analyzer.links.get("external", [])

        bad_links = 0
        for link in all_links:
            text = link.get("text", "").strip().lower()
            if text in bad_texts:
                bad_links += 1

        if bad_links > 0:
            result.add_issue("warning", "accessibility", f"[WCAG 2.4.4] {bad_links}个链接文本不具描述性", 2)
        elif all_links:
            result.add_pass("accessibility", "[WCAG 2.4.4] 链接文本检查通过")

    def _check_color_contrast_hints(self, result, analyzer):
        """Heuristic contrast check based on inline styles."""
        html = analyzer.html_raw
        # Look for common low-contrast patterns in inline styles
        light_on_light = re.findall(r'color:\s*#[cdefCDEF]{3,6}', html)
        if light_on_light:
            result.add_issue("warning", "accessibility",
                f"[WCAG 1.4.3] 检测到{len(light_on_light)}处可能的低对比度颜色", 2)
        else:
            result.add_pass("accessibility", "[WCAG 1.4.3] 未检测到明显低对比度问题")

    def _check_focus_management(self, result, analyzer):
        if analyzer.tab_index_elements > 0:
            result.add_pass("accessibility", f"[WCAG 2.4.3] {analyzer.tab_index_elements}个元素设置了tabindex")
        # Check for tabindex > 0 which is bad practice
        html = analyzer.html_raw
        bad_tabindex = re.findall(r'tabindex=["\']([2-9]|\d{2,})["\']', html)
        if bad_tabindex:
            result.add_issue("warning", "accessibility",
                f"[WCAG 2.4.3] {len(bad_tabindex)}个元素使用了正值tabindex (不推荐)", 1)
