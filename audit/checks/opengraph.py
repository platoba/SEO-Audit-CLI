"""Open Graph & Twitter Card validator."""

import re
from .base import BaseCheck


class OpenGraphCheck(BaseCheck):
    """Validate Open Graph and Twitter Card metadata."""
    name = "opengraph"
    description = "Open Graph + Twitter Card meta tag validation"

    OG_REQUIRED = ["og:title", "og:description", "og:image", "og:url", "og:type"]
    OG_OPTIONAL = ["og:site_name", "og:locale", "og:image:width", "og:image:height", "og:image:alt"]
    TWITTER_TAGS = ["twitter:card", "twitter:title", "twitter:description", "twitter:image"]

    def run(self, result, response, analyzer):
        meta = analyzer.meta
        og_data = {}
        tw_data = {}
        og_issues = []
        tw_issues = []

        # Collect OG tags
        for key in self.OG_REQUIRED + self.OG_OPTIONAL:
            value = meta.get(key, "")
            if value:
                og_data[key] = value

        # Collect Twitter tags
        for key in self.TWITTER_TAGS:
            value = meta.get(key, "")
            if value:
                tw_data[key] = value

        result.details["opengraph"] = {
            "og_tags": og_data,
            "twitter_tags": tw_data,
        }

        # --- Open Graph validation ---
        present_required = [k for k in self.OG_REQUIRED if k in og_data]
        missing_required = [k for k in self.OG_REQUIRED if k not in og_data]

        if not og_data:
            result.add_issue("error", "opengraph", "缺少所有Open Graph标签，社交分享效果差", 5)
        elif missing_required:
            missing_str = ", ".join(missing_required)
            result.add_issue("warning", "opengraph",
                             f"缺少OG必要标签: {missing_str}", len(missing_required))
        else:
            result.add_pass("opengraph", f"Open Graph标签完整 ({len(og_data)}个)")

        # OG title length
        og_title = og_data.get("og:title", "")
        if og_title:
            if len(og_title) > 90:
                result.add_issue("warning", "opengraph", f"og:title过长 ({len(og_title)}字符)，建议60字以内", 1)
            elif len(og_title) < 10:
                result.add_issue("warning", "opengraph", f"og:title过短 ({len(og_title)}字符)", 1)

        # OG description length
        og_desc = og_data.get("og:description", "")
        if og_desc and len(og_desc) > 200:
            result.add_issue("info", "opengraph", f"og:description较长 ({len(og_desc)}字符)，可能被截断")

        # OG image
        og_image = og_data.get("og:image", "")
        if og_image:
            if not og_image.startswith(("http://", "https://")):
                result.add_issue("warning", "opengraph", "og:image应使用完整URL(https://...)", 1)
            result.add_pass("opengraph", "og:image已设置")
        else:
            result.add_issue("warning", "opengraph", "缺少og:image，社交分享无预览图", 3)

        # OG image dimensions
        if "og:image:width" not in og_data or "og:image:height" not in og_data:
            if og_image:
                result.add_issue("info", "opengraph", "建议添加og:image:width和og:image:height")

        # --- Twitter Card validation ---
        if not tw_data:
            result.add_issue("warning", "opengraph", "缺少Twitter Card标签", 2)
        else:
            card_type = tw_data.get("twitter:card", "")
            valid_types = ("summary", "summary_large_image", "app", "player")
            if card_type and card_type not in valid_types:
                result.add_issue("warning", "opengraph", f"twitter:card类型无效: {card_type}", 1)
            else:
                result.add_pass("opengraph", f"Twitter Card配置正确 (type: {card_type})")

            missing_tw = [k for k in self.TWITTER_TAGS if k not in tw_data]
            if missing_tw:
                result.add_issue("info", "opengraph", f"缺少Twitter标签: {', '.join(missing_tw)}")

        # OG vs page title consistency
        if og_title and analyzer.title:
            # They don't need to be identical, but shouldn't be drastically different
            og_words = set(og_title.lower().split())
            title_words = set(analyzer.title.lower().split())
            overlap = og_words & title_words
            if len(overlap) == 0 and len(og_words) > 2 and len(title_words) > 2:
                result.add_issue("info", "opengraph", "og:title与页面title完全不同，检查是否正确")
