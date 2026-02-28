"""
社交媒体 SEO 检查
OG tags, Twitter cards, 社交分享优化
"""

from audit.checks.base import BaseCheck


class SocialCheck(BaseCheck):
    """
    社交媒体元数据检查
    - Open Graph (og:title, og:description, og:image, og:url, og:type)
    - Twitter Cards (twitter:card, twitter:title, twitter:description, twitter:image)
    """

    name = "social"
    description = "Social media meta tags (OG + Twitter Cards)"

    OG_REQUIRED = ["og:title", "og:description", "og:image"]
    OG_RECOMMENDED = ["og:url", "og:type", "og:site_name"]
    TWITTER_REQUIRED = ["twitter:card"]
    TWITTER_RECOMMENDED = ["twitter:title", "twitter:description", "twitter:image"]

    def run(self, result, response, analyzer):
        meta = {}
        for m in getattr(analyzer, "meta_tags", []):
            prop = m.get("property", "") or m.get("name", "")
            content = m.get("content", "")
            if prop:
                meta[prop.lower()] = content

        self._check_og(result, meta)
        self._check_twitter(result, meta)

    def _check_og(self, result, meta):
        """Open Graph 检查"""
        missing = [tag for tag in self.OG_REQUIRED if tag not in meta]
        if missing:
            result.add_issue(
                "error", "social",
                f"Missing required OG tags: {', '.join(missing)}",
                deduction=5,
            )
        else:
            result.add_pass("social", "All required OG tags present")

        # 检查og:image尺寸建议
        if "og:image" in meta:
            img_url = meta["og:image"]
            if not img_url.startswith("http"):
                result.add_issue(
                    "warning", "social",
                    "og:image should use absolute URL",
                    deduction=2,
                )

            if "og:image:width" not in meta or "og:image:height" not in meta:
                result.add_issue(
                    "info", "social",
                    "Consider adding og:image:width and og:image:height for faster rendering",
                    deduction=0,
                )

        # 推荐标签
        missing_rec = [tag for tag in self.OG_RECOMMENDED if tag not in meta]
        if missing_rec:
            result.add_issue(
                "info", "social",
                f"Recommended OG tags missing: {', '.join(missing_rec)}",
                deduction=0,
            )

        # og:description 长度检查
        og_desc = meta.get("og:description", "")
        if og_desc and len(og_desc) > 200:
            result.add_issue(
                "warning", "social",
                f"og:description too long ({len(og_desc)} chars, recommended < 200)",
                deduction=1,
            )

    def _check_twitter(self, result, meta):
        """Twitter Card 检查"""
        if "twitter:card" not in meta:
            result.add_issue(
                "warning", "social",
                "Missing twitter:card meta tag",
                deduction=3,
            )
        else:
            card_type = meta["twitter:card"]
            valid_types = ["summary", "summary_large_image", "app", "player"]
            if card_type not in valid_types:
                result.add_issue(
                    "warning", "social",
                    f"Invalid twitter:card type: '{card_type}' (valid: {', '.join(valid_types)})",
                    deduction=2,
                )
            else:
                result.add_pass("social", f"Twitter card type: {card_type}")

        # Twitter 推荐标签 (如果没有OG fallback)
        missing_tw = []
        for tag in self.TWITTER_RECOMMENDED:
            og_equiv = tag.replace("twitter:", "og:")
            if tag not in meta and og_equiv not in meta:
                missing_tw.append(tag)

        if missing_tw:
            result.add_issue(
                "info", "social",
                f"Missing Twitter tags (no OG fallback): {', '.join(missing_tw)}",
                deduction=0,
            )
