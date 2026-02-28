"""Export audit results to CSV, JSON, and summary formats."""

import csv
import json
import io
from typing import List, Optional
from ..core import AuditResult


class AuditExporter:
    """Export audit results in multiple formats."""

    @staticmethod
    def to_json(results: List[AuditResult], indent: int = 2) -> str:
        """Export results as JSON."""
        data = [r.to_dict() for r in results]
        return json.dumps(data, indent=indent, ensure_ascii=False, default=str)

    @staticmethod
    def to_csv(results: List[AuditResult]) -> str:
        """Export results as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "URL", "Domain", "Score", "Grade", "Status Code",
            "Load Time (s)", "Errors", "Warnings", "Passed",
            "Title", "Meta Description", "Timestamp",
        ])

        for r in results:
            writer.writerow([
                r.url, r.domain, r.score, r.grade, r.status_code,
                r.load_time, len(r.errors), len(r.warnings), len(r.passed),
                r.title[:100], r.meta_description[:100], r.timestamp,
            ])

        return output.getvalue()

    @staticmethod
    def to_jsonl(results: List[AuditResult]) -> str:
        """Export results as JSON Lines (one JSON per line)."""
        lines = []
        for r in results:
            lines.append(json.dumps(r.to_dict(), ensure_ascii=False, default=str))
        return "\n".join(lines)

    @staticmethod
    def to_summary(results: List[AuditResult]) -> str:
        """Generate a text summary report."""
        if not results:
            return "No results to summarize."

        scores = [r.score for r in results]
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)
        load_times = [r.load_time for r in results if r.load_time > 0]
        avg_load = sum(load_times) / len(load_times) if load_times else 0

        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)

        # Grade distribution
        grades = {}
        for r in results:
            g = r.grade
            grades[g] = grades.get(g, 0) + 1

        lines = [
            "=" * 60,
            "SEO Audit Summary Report",
            "=" * 60,
            f"URLs audited: {len(results)}",
            f"Average score: {avg_score:.1f}/100",
            f"Score range: {min_score} - {max_score}",
            f"Average load time: {avg_load:.2f}s",
            f"Total errors: {total_errors}",
            f"Total warnings: {total_warnings}",
            "",
            "Grade Distribution:",
        ]

        for grade in ["A+", "A", "B", "C", "D", "F"]:
            count = grades.get(grade, 0)
            if count:
                bar = "█" * count
                lines.append(f"  {grade:>2}: {bar} ({count})")

        lines.extend(["", "Top Issues:"])

        # Aggregate issues by message
        issue_counts = {}
        for r in results:
            for issue in r.errors + r.warnings:
                msg = issue.message
                issue_counts[msg] = issue_counts.get(msg, 0) + 1

        for msg, count in sorted(issue_counts.items(), key=lambda x: -x[1])[:10]:
            lines.append(f"  [{count}x] {msg}")

        lines.extend([
            "",
            "Worst Performers:",
        ])
        for r in sorted(results, key=lambda x: x.score)[:5]:
            lines.append(f"  {r.score}/100 | {r.url}")

        lines.append("=" * 60)
        return "\n".join(lines)

    @staticmethod
    def save(content: str, filepath: str) -> str:
        """Save export content to file."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath
