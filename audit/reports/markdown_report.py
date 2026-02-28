"""
Markdown 报告生成器
"""

import time
from typing import Optional
from audit.core import AuditResult


class MarkdownReport:
    """生成 Markdown 格式的 SEO 审计报告"""

    def generate(self, result: AuditResult) -> str:
        lines = [
            f"# SEO Audit Report: {result.domain}",
            f"**URL:** {result.url}",
            f"**Date:** {result.timestamp or time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Score:** {result.score}/100 ({result.grade})",
            f"**Load Time:** {result.load_time:.2f}s",
            "",
            "---",
            "",
        ]

        # Summary
        lines.append("## Summary\n")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Score | {result.score}/100 |")
        lines.append(f"| Grade | {result.grade} |")
        lines.append(f"| Errors | {len(result.errors)} |")
        lines.append(f"| Warnings | {len(result.warnings)} |")
        lines.append(f"| Status Code | {result.status_code} |")
        lines.append(f"| Load Time | {result.load_time:.2f}s |")
        lines.append("")

        # Errors
        if result.errors:
            lines.append("## ❌ Errors\n")
            for issue in result.errors:
                lines.append(f"- **[{issue.category}]** {issue.message} (-{issue.deduction})")
            lines.append("")

        # Warnings
        if result.warnings:
            lines.append("## ⚠️ Warnings\n")
            for issue in result.warnings:
                lines.append(f"- **[{issue.category}]** {issue.message} (-{issue.deduction})")
            lines.append("")

        # Passed
        passed = [i for i in result.issues if i.severity == "pass"]
        if passed:
            lines.append("## ✅ Passed\n")
            for issue in passed:
                lines.append(f"- [{issue.category}] {issue.message}")
            lines.append("")

        # Info
        info = [i for i in result.issues if i.severity == "info"]
        if info:
            lines.append("## ℹ️ Info\n")
            for issue in info:
                lines.append(f"- [{issue.category}] {issue.message}")
            lines.append("")

        return "\n".join(lines)
