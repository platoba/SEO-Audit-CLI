"""Redirect chain analyzer - detect chains, loops, and mixed-protocol redirects."""

import requests
from typing import List, Dict, Tuple
from .base import BaseCheck


class RedirectChainAnalyzer:
    """Analyze redirect chains for a URL."""

    MAX_REDIRECTS = 20

    def __init__(self, url: str, timeout: int = 10):
        self.url = url
        self.timeout = timeout
        self.chain: List[Dict] = []
        self.has_loop = False
        self.final_url = url

    def trace(self) -> "RedirectChainAnalyzer":
        """Trace the full redirect chain."""
        visited = set()
        current_url = self.url

        for i in range(self.MAX_REDIRECTS):
            if current_url in visited:
                self.has_loop = True
                self.chain.append({
                    "url": current_url,
                    "status": 0,
                    "type": "loop",
                    "hop": i + 1,
                })
                break

            visited.add(current_url)

            try:
                r = requests.get(
                    current_url,
                    timeout=self.timeout,
                    allow_redirects=False,
                    headers={"User-Agent": "SEO-Audit-CLI/3.0"},
                )

                hop = {
                    "url": current_url,
                    "status": r.status_code,
                    "hop": i + 1,
                }

                if r.status_code in (301, 302, 303, 307, 308):
                    location = r.headers.get("Location", "")
                    hop["redirect_to"] = location
                    hop["type"] = "permanent" if r.status_code in (301, 308) else "temporary"
                    self.chain.append(hop)
                    current_url = location
                else:
                    hop["type"] = "final"
                    self.chain.append(hop)
                    self.final_url = current_url
                    break

            except Exception as e:
                self.chain.append({
                    "url": current_url,
                    "status": 0,
                    "type": "error",
                    "error": str(e),
                    "hop": i + 1,
                })
                break

        return self

    @property
    def hop_count(self) -> int:
        return len(self.chain) - 1 if self.chain else 0

    @property
    def has_mixed_protocol(self) -> bool:
        """Check for HTTP→HTTPS or HTTPS→HTTP redirects."""
        urls = [h["url"] for h in self.chain]
        protocols = [u.split("://")[0] for u in urls if "://" in u]
        return len(set(protocols)) > 1

    @property
    def has_temporary_redirects(self) -> bool:
        return any(h.get("type") == "temporary" for h in self.chain)

    @property
    def permanent_only(self) -> bool:
        redirects = [h for h in self.chain if h.get("type") in ("permanent", "temporary")]
        return all(h["type"] == "permanent" for h in redirects)


class RedirectCheck(BaseCheck):
    """Redirect chain analysis for SEO."""
    name = "redirects"
    description = "Redirect chain detection, loop analysis, protocol checks"

    def run(self, result, response, analyzer):
        # Check redirect history from the original response
        if hasattr(response, "history") and response.history:
            chain_len = len(response.history)
            result.details["redirects"] = {
                "count": chain_len,
                "chain": [
                    {
                        "url": r.url,
                        "status": r.status_code,
                    }
                    for r in response.history
                ],
                "final_url": response.url,
            }

            if chain_len == 1:
                first = response.history[0]
                if first.status_code in (301, 308):
                    result.add_pass("redirects", f"单次{first.status_code}永久重定向 → {response.url}")
                elif first.status_code in (302, 307):
                    result.add_issue("warning", "redirects",
                                     f"使用临时重定向({first.status_code})而非永久重定向(301)，不利于SEO", 3)
            elif chain_len == 2:
                result.add_issue("warning", "redirects", f"存在{chain_len}次重定向跳转，建议减少", 2)
            elif chain_len >= 3:
                result.add_issue("error", "redirects",
                                 f"重定向链过长({chain_len}次)，严重影响SEO和加载速度", 5)

            # Mixed protocol check
            all_urls = [r.url for r in response.history] + [response.url]
            protocols = set(u.split("://")[0] for u in all_urls if "://" in u)
            if "http" in protocols and "https" in protocols:
                result.add_issue("warning", "redirects", "重定向链中存在HTTP→HTTPS混合协议", 2)

            # Check for temporary redirects in chain
            temp_redirects = [r for r in response.history if r.status_code in (302, 303, 307)]
            if temp_redirects:
                result.add_issue("warning", "redirects",
                                 f"重定向链中有{len(temp_redirects)}个临时重定向，建议改为301", 2)
        else:
            result.add_pass("redirects", "无重定向，直接访问目标URL")
            result.details["redirects"] = {"count": 0, "chain": [], "final_url": result.url}

        # Check canonical vs actual URL
        canonical = analyzer.meta.get("canonical", "") or ""
        if canonical and canonical != result.url and canonical != response.url:
            result.add_issue("warning", "redirects",
                             f"canonical URL ({canonical[:80]}) 与实际URL不同", 2)
