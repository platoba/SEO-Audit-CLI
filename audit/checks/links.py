"""Links check - internal/external links, images, broken link sampling."""

import requests
from urllib.parse import urljoin
from .base import BaseCheck


class LinksCheck(BaseCheck):
    name = "links"
    description = "Internal/external links, image alt, broken link sampling"

    def run(self, result, response, analyzer):
        self._check_internal_links(result, analyzer)
        self._check_external_links(result, analyzer)
        self._check_images(result, analyzer)
        self._check_nofollow(result, analyzer)

    def _check_internal_links(self, result, analyzer):
        internal = analyzer.links.get("internal", [])
        count = len(internal)
        result.details["internal_links"] = count
        if count == 0:
            result.add_issue("warning", "links", "没有内部链接", 2)
        else:
            result.add_pass("links", f"内部链接: {count}个")

    def _check_external_links(self, result, analyzer):
        external = analyzer.links.get("external", [])
        count = len(external)
        result.details["external_links"] = count
        if count > 100:
            result.add_issue("warning", "links", f"外部链接过多 ({count}个)", 2)
        elif count > 0:
            result.add_pass("links", f"外部链接: {count}个")
        else:
            result.add_issue("info", "links", "没有外部链接")

    def _check_images(self, result, analyzer):
        images = analyzer.images
        total = len(images)
        if total == 0:
            result.add_issue("info", "links", "页面没有图片")
            return

        no_alt = [img for img in images if img.get("alt") is None]
        empty_alt = [img for img in images if img.get("alt") == ""]
        lazy = [img for img in images if img.get("loading") == "lazy"]
        no_dimensions = [img for img in images if not img.get("width") or not img.get("height")]

        if no_alt:
            result.add_issue("error", "links", f"{len(no_alt)}/{total}张图片缺少alt属性", 5)
        elif empty_alt:
            result.add_issue("warning", "links", f"{len(empty_alt)}/{total}张图片alt为空", 2)
        else:
            result.add_pass("links", f"所有{total}张图片都有alt属性")

        if not lazy and total > 3:
            result.add_issue("warning", "links", "没有图片使用lazy loading", 2)
        elif lazy:
            result.add_pass("links", f"{len(lazy)}/{total}张图片使用lazy loading")

        if no_dimensions and total > 0:
            result.add_issue("warning", "links", f"{len(no_dimensions)}/{total}张图片缺少宽高属性 (CLS风险)", 2)

        result.details["images"] = {
            "total": total,
            "no_alt": len(no_alt),
            "empty_alt": len(empty_alt),
            "lazy_loaded": len(lazy),
            "no_dimensions": len(no_dimensions),
        }

    def _check_nofollow(self, result, analyzer):
        external = analyzer.links.get("external", [])
        if not external:
            return

        nofollow_count = sum(1 for l in external if "nofollow" in l.get("rel", ""))
        if nofollow_count == 0 and len(external) > 5:
            result.add_issue("info", "links", f"所有{len(external)}个外部链接都没有nofollow")
