"""Meta tags check - title, description, OG, canonical, robots."""

from .base import BaseCheck


class MetaCheck(BaseCheck):
    name = "meta"
    description = "Title, description, Open Graph, canonical, robots meta"

    def run(self, result, response, analyzer):
        self._check_title(result, analyzer)
        self._check_description(result, analyzer)
        self._check_canonical(result, analyzer)
        self._check_open_graph(result, analyzer)
        self._check_twitter_card(result, analyzer)
        self._check_robots_meta(result, analyzer)
        self._check_headings(result, analyzer)
        self._check_lang(result, analyzer)

    def _check_title(self, result, analyzer):
        title = analyzer.title.strip()
        if not title:
            result.add_issue("error", "meta", "缺少<title>标签", 10)
        elif len(title) < 10:
            result.add_issue("warning", "meta", f"标题太短 ({len(title)}字符，建议30-60)", 2)
        elif len(title) > 60:
            result.add_issue("warning", "meta", f"标题太长 ({len(title)}字符，建议30-60)", 2)
        else:
            result.add_pass("meta", f"标题长度OK ({len(title)}字符)")

    def _check_description(self, result, analyzer):
        desc = analyzer.meta.get("description", "")
        if not desc:
            result.add_issue("error", "meta", "缺少meta description", 8)
        elif len(desc) < 50:
            result.add_issue("warning", "meta", f"描述太短 ({len(desc)}字符，建议120-155)", 2)
        elif len(desc) > 160:
            result.add_issue("warning", "meta", f"描述太长 ({len(desc)}字符，建议120-155)", 2)
        else:
            result.add_pass("meta", f"描述长度OK ({len(desc)}字符)")

    def _check_canonical(self, result, analyzer):
        html = analyzer.html_raw.lower()
        if 'rel="canonical"' in html or "rel='canonical'" in html:
            result.add_pass("meta", "有canonical标签")
        else:
            result.add_issue("warning", "meta", "缺少canonical标签", 2)

    def _check_open_graph(self, result, analyzer):
        og_title = analyzer.meta.get("og:title", "")
        og_desc = analyzer.meta.get("og:description", "")
        og_image = analyzer.meta.get("og:image", "")

        missing = []
        if not og_title:
            missing.append("og:title")
        if not og_desc:
            missing.append("og:description")
        if not og_image:
            missing.append("og:image")

        if not missing:
            result.add_pass("meta", "Open Graph标签完整")
        elif len(missing) == 3:
            result.add_issue("warning", "meta", "缺少Open Graph标签", 3)
        else:
            result.add_issue("warning", "meta", f"缺少OG标签: {', '.join(missing)}", 2)

        result.details["og_tags"] = {"title": og_title, "description": og_desc, "image": og_image}

    def _check_twitter_card(self, result, analyzer):
        tc = analyzer.meta.get("twitter:card", "")
        if tc:
            result.add_pass("meta", f"Twitter Card: {tc}")
        else:
            result.add_issue("info", "meta", "缺少Twitter Card标签")

    def _check_robots_meta(self, result, analyzer):
        robots = analyzer.meta.get("robots", "")
        if robots:
            result.details["robots_meta"] = robots
            if "noindex" in robots.lower():
                result.add_issue("warning", "meta", f"robots meta包含noindex: {robots}", 5)
            elif "nofollow" in robots.lower():
                result.add_issue("info", "meta", f"robots meta包含nofollow: {robots}")
            else:
                result.add_pass("meta", f"robots meta: {robots}")

    def _check_headings(self, result, analyzer):
        h1s = analyzer.headings.get("h1", [])
        if not h1s:
            result.add_issue("error", "meta", "缺少H1标签", 8)
        elif len(h1s) > 1:
            result.add_issue("warning", "meta", f"多个H1标签 ({len(h1s)}个，建议1个)", 2)
        else:
            result.add_pass("meta", f"H1标签OK: {h1s[0][:50]}")

        # Check heading hierarchy
        prev_level = 0
        skip_found = False
        for i in range(1, 7):
            tag = f"h{i}"
            if analyzer.headings.get(tag):
                if i > prev_level + 1 and prev_level > 0:
                    skip_found = True
                prev_level = i

        if skip_found:
            result.add_issue("warning", "meta", "标题层级跳跃 (如H1直接到H3)", 1)
        elif prev_level > 0:
            result.add_pass("meta", "标题层级结构正常")

        result.details["headings"] = {k: v for k, v in analyzer.headings.items() if v}

    def _check_lang(self, result, analyzer):
        if analyzer.lang:
            result.add_pass("meta", f"HTML lang属性: {analyzer.lang}")
        else:
            result.add_issue("warning", "meta", "缺少HTML lang属性", 2)
