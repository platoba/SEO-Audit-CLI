"""
多语言 SEO 检查
hreflang, lang属性, 国际化最佳实践
"""

import re
from audit.checks.base import BaseCheck


class I18nCheck(BaseCheck):
    """
    多语言/国际化 SEO 检查
    - html lang 属性
    - hreflang 标签
    - Content-Language header
    - 编码声明
    """

    name = "i18n"
    description = "Internationalization & multilingual SEO"

    VALID_LANG_PATTERN = re.compile(r'^[a-z]{2}(-[A-Z]{2})?$')

    def run(self, result, response, analyzer):
        self._check_lang_attr(result, analyzer)
        self._check_hreflang(result, response, analyzer)
        self._check_content_language(result, response)
        self._check_charset(result, response, analyzer)

    def _check_lang_attr(self, result, analyzer):
        """检查 <html lang="..."> 属性"""
        lang = getattr(analyzer, "html_lang", None) or ""

        if not lang:
            result.add_issue(
                "error", "i18n",
                "Missing <html lang='...'> attribute — essential for accessibility and SEO",
                deduction=5,
            )
        elif not self.VALID_LANG_PATTERN.match(lang):
            result.add_issue(
                "warning", "i18n",
                f"Invalid lang attribute: '{lang}' — expected format: 'en' or 'en-US'",
                deduction=2,
            )
        else:
            result.add_pass("i18n", f"HTML lang attribute: '{lang}'")

    def _check_hreflang(self, result, response, analyzer):
        """检查 hreflang 标签"""
        hreflangs = []
        for link in getattr(analyzer, "links", []):
            if link.get("rel") == "alternate" and link.get("hreflang"):
                hreflangs.append(link)

        # Also check Link header
        link_header = response.headers.get("Link", "")
        if 'hreflang' in link_header:
            hreflangs.append({"source": "header"})

        if not hreflangs:
            result.add_issue(
                "info", "i18n",
                "No hreflang tags found — add if page is available in multiple languages",
                deduction=0,
            )
            return

        # Check for x-default
        has_default = any(
            h.get("hreflang") == "x-default" for h in hreflangs
        )
        if not has_default:
            result.add_issue(
                "warning", "i18n",
                "Missing hreflang='x-default' — recommended for language fallback",
                deduction=2,
            )

        # Check for self-referencing hreflang
        html_lang = getattr(analyzer, "html_lang", "")
        has_self = any(
            h.get("hreflang", "").startswith(html_lang)
            for h in hreflangs
            if html_lang
        )
        if html_lang and not has_self:
            result.add_issue(
                "warning", "i18n",
                "Missing self-referencing hreflang tag for current language",
                deduction=1,
            )

        result.add_pass("i18n", f"{len(hreflangs)} hreflang tag(s) found")

    def _check_content_language(self, result, response):
        """检查 Content-Language header"""
        content_lang = response.headers.get("Content-Language", "")
        if content_lang:
            result.add_pass("i18n", f"Content-Language header: '{content_lang}'")
        # Not deducting — it's optional

    def _check_charset(self, result, response, analyzer):
        """检查字符编码"""
        meta_tags = getattr(analyzer, "meta_tags", [])
        has_charset = any(
            m.get("charset") or m.get("http-equiv", "").lower() == "content-type"
            for m in meta_tags
        )

        if not has_charset:
            result.add_issue(
                "warning", "i18n",
                "Missing <meta charset='UTF-8'> — important for international content",
                deduction=2,
            )
        else:
            result.add_pass("i18n", "Character encoding declared")
