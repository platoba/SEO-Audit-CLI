"""Robots.txt deep analyzer - parse directives, detect issues, validate sitemaps."""

import re
import requests
from typing import Dict, List, Optional
from .base import BaseCheck


class RobotsAnalyzer:
    """Parse and analyze robots.txt content."""

    def __init__(self, content: str):
        self.content = content
        self.rules: Dict[str, List[Dict]] = {}  # user-agent -> [rules]
        self.sitemaps: List[str] = []
        self.crawl_delay: Dict[str, float] = {}
        self.host: Optional[str] = None
        self._parse()

    def _parse(self):
        current_agents = ["*"]
        for line in self.content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(":", 1)
            if len(parts) != 2:
                continue

            directive = parts[0].strip().lower()
            value = parts[1].strip()

            if directive == "user-agent":
                current_agents = [value]
                for agent in current_agents:
                    if agent not in self.rules:
                        self.rules[agent] = []
            elif directive == "disallow":
                for agent in current_agents:
                    self.rules.setdefault(agent, []).append({"type": "disallow", "path": value})
            elif directive == "allow":
                for agent in current_agents:
                    self.rules.setdefault(agent, []).append({"type": "allow", "path": value})
            elif directive == "sitemap":
                self.sitemaps.append(value)
            elif directive == "crawl-delay":
                try:
                    delay = float(value)
                    for agent in current_agents:
                        self.crawl_delay[agent] = delay
                except ValueError:
                    pass
            elif directive == "host":
                self.host = value

    @property
    def total_rules(self) -> int:
        return sum(len(rules) for rules in self.rules.values())

    @property
    def disallow_count(self) -> int:
        return sum(1 for rules in self.rules.values() for r in rules if r["type"] == "disallow" and r["path"])

    @property
    def blocked_paths(self) -> List[str]:
        """Get all blocked paths for default user-agent (*)."""
        wildcard_rules = self.rules.get("*", [])
        return [r["path"] for r in wildcard_rules if r["type"] == "disallow" and r["path"]]

    def is_path_blocked(self, path: str, user_agent: str = "*") -> bool:
        """Check if a path is blocked for a given user agent."""
        rules = self.rules.get(user_agent, self.rules.get("*", []))
        blocked = False
        for rule in rules:
            if rule["path"] and path.startswith(rule["path"]):
                if rule["type"] == "disallow":
                    blocked = True
                elif rule["type"] == "allow":
                    blocked = False
        return blocked


class RobotsCheck(BaseCheck):
    """Deep robots.txt analysis."""
    name = "robots"
    description = "Robots.txt validation, directive analysis, sitemap discovery"

    CRITICAL_PATHS = ["/", "/api/", "/admin/", "/wp-admin/"]
    SEO_IMPORTANT_PATHS = ["/products/", "/blog/", "/category/", "/tag/"]

    def run(self, result, response, analyzer):
        try:
            robots_url = f"https://{result.domain}/robots.txt"
            r = requests.get(robots_url, timeout=5, headers={"User-Agent": "SEO-Audit-CLI/3.0"})

            if not r.ok:
                result.add_issue("warning", "robots", "robots.txt不存在或不可访问 (HTTP {})".format(r.status_code), 3)
                result.details["robots"] = {"exists": False}
                return

            content = r.text
            if len(content.strip()) == 0:
                result.add_issue("warning", "robots", "robots.txt为空", 2)
                result.details["robots"] = {"exists": True, "empty": True}
                return

            parsed = RobotsAnalyzer(content)
            details = {
                "exists": True,
                "size_bytes": len(content),
                "user_agents": list(parsed.rules.keys()),
                "total_rules": parsed.total_rules,
                "disallow_count": parsed.disallow_count,
                "sitemaps": parsed.sitemaps,
                "crawl_delay": parsed.crawl_delay,
                "blocked_paths": parsed.blocked_paths,
            }
            result.details["robots"] = details
            result.add_pass("robots", f"robots.txt存在 ({len(content)}字节, {parsed.total_rules}条规则)")

            # Check for overly permissive (empty disallow = allow all)
            wildcard_rules = parsed.rules.get("*", [])
            if wildcard_rules and all(not r["path"] for r in wildcard_rules if r["type"] == "disallow"):
                result.add_issue("info", "robots", "robots.txt对所有爬虫完全开放")

            # Check for blocking everything
            if parsed.is_path_blocked("/"):
                result.add_issue("error", "robots", "robots.txt阻止了根路径 /，搜索引擎无法抓取！", 15)

            # Check for blocking important SEO paths
            for path in self.SEO_IMPORTANT_PATHS:
                if parsed.is_path_blocked(path):
                    result.add_issue("warning", "robots", f"robots.txt阻止了SEO重要路径: {path}", 2)

            # Sitemap references
            if parsed.sitemaps:
                result.add_pass("robots", f"robots.txt声明了{len(parsed.sitemaps)}个sitemap")
                # Validate sitemap accessibility
                for sm_url in parsed.sitemaps[:3]:
                    try:
                        sm_r = requests.get(sm_url, timeout=5, headers={"User-Agent": "SEO-Audit-CLI/3.0"})
                        if not sm_r.ok:
                            result.add_issue("warning", "robots", f"sitemap不可访问: {sm_url} (HTTP {sm_r.status_code})", 2)
                    except Exception:
                        result.add_issue("warning", "robots", f"sitemap连接失败: {sm_url}", 1)
            else:
                result.add_issue("warning", "robots", "robots.txt未声明sitemap", 2)

            # Crawl delay warnings
            if parsed.crawl_delay:
                for agent, delay in parsed.crawl_delay.items():
                    if delay > 10:
                        result.add_issue("warning", "robots", f"crawl-delay过大({delay}s)，可能影响收录速度", 2)
                    else:
                        result.add_issue("info", "robots", f"crawl-delay: {delay}s (user-agent: {agent})")

            # Size check
            if len(content) > 512000:
                result.add_issue("warning", "robots", f"robots.txt过大 ({len(content)//1024}KB)，建议精简", 1)

        except requests.exceptions.Timeout:
            result.add_issue("warning", "robots", "robots.txt请求超时", 1)
        except Exception as e:
            result.add_issue("info", "robots", f"robots.txt检查异常: {type(e).__name__}")
