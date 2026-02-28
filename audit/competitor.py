"""
竞品 SEO 对比分析
"""

import time
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from audit.core import AuditResult, AuditEngine


@dataclass
class CompetitorResult:
    """竞品对比结果"""
    target: AuditResult
    competitors: List[AuditResult] = field(default_factory=list)
    comparison: Dict = field(default_factory=dict)
    timestamp: float = 0.0

    def to_report(self) -> str:
        """生成对比报告"""
        lines = [
            f"# SEO Competitor Comparison",
            f"*Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n",
            "| Site | Score | Grade | Issues | Load Time |",
            "|------|-------|-------|--------|-----------|",
        ]

        all_results = [self.target] + self.competitors
        for r in all_results:
            marker = "→ " if r == self.target else "  "
            lines.append(
                f"| {marker}{r.domain} | {r.score} | {r.grade} | "
                f"{len(r.errors)}E/{len(r.warnings)}W | {r.load_time:.2f}s |"
            )

        lines.append("")

        # 分类对比
        if self.comparison:
            lines.append("## Category Breakdown\n")
            for category, scores in self.comparison.items():
                lines.append(f"### {category}")
                for domain, score in scores.items():
                    lines.append(f"  - {domain}: {score}")
                lines.append("")

        return "\n".join(lines)


class CompetitorAnalyzer:
    """
    竞品SEO对比分析器
    同时审计多个站点并生成对比
    """

    def __init__(self, engine: Optional[AuditEngine] = None):
        self.engine = engine or AuditEngine()

    def compare(
        self,
        target_url: str,
        competitor_urls: List[str],
    ) -> CompetitorResult:
        """
        对比目标站点与竞品

        Args:
            target_url: 目标站点URL
            competitor_urls: 竞品URL列表

        Returns:
            CompetitorResult
        """
        target_result = self.engine.audit(target_url)

        comp_results = []
        for url in competitor_urls:
            try:
                r = self.engine.audit(url)
                comp_results.append(r)
            except Exception:
                pass

        # 生成对比数据
        comparison = self._build_comparison(target_result, comp_results)

        return CompetitorResult(
            target=target_result,
            competitors=comp_results,
            comparison=comparison,
            timestamp=time.time(),
        )

    def _build_comparison(
        self,
        target: AuditResult,
        competitors: List[AuditResult],
    ) -> Dict:
        """构建分类对比"""
        all_results = [target] + competitors
        categories = set()
        for r in all_results:
            for issue in r.issues:
                categories.add(issue.category)

        comparison = {}
        for cat in sorted(categories):
            comparison[cat] = {}
            for r in all_results:
                cat_issues = [i for i in r.issues if i.category == cat]
                errors = sum(1 for i in cat_issues if i.severity == "error")
                warnings = sum(1 for i in cat_issues if i.severity == "warning")
                passes = sum(1 for i in cat_issues if i.severity == "pass")
                comparison[cat][r.domain] = f"{passes}✓ {errors}✗ {warnings}⚠"

        return comparison

    def quick_compare(self, urls: List[str]) -> str:
        """快速对比多个URL，返回文本报告"""
        if not urls:
            return "No URLs provided"

        results = []
        for url in urls:
            try:
                r = self.engine.audit(url)
                results.append(r)
            except Exception as e:
                results.append(AuditResult(url=url, domain=url, score=0))

        # 排序: 高分在前
        results.sort(key=lambda r: r.score, reverse=True)

        lines = ["📊 *SEO Quick Comparison*\n"]
        for i, r in enumerate(results, 1):
            medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
            lines.append(
                f"{medal} `{r.domain}` — Score: **{r.score}** ({r.grade}) "
                f"| {len(r.errors)}E {len(r.warnings)}W | {r.load_time:.2f}s"
            )

        return "\n".join(lines)
