"""Competitor comparison - side-by-side audit of two sites."""

from typing import Dict, Any, Optional
from .core import AuditEngine, AuditResult


def compare_sites(url_a: str, url_b: str, engine: Optional[AuditEngine] = None) -> Dict[str, Any]:
    """Compare two sites side by side, return comparison dict."""
    if engine is None:
        engine = AuditEngine()

    result_a = engine.audit(url_a)
    result_b = engine.audit(url_b)

    comparison = {
        "site_a": result_a.to_dict(),
        "site_b": result_b.to_dict(),
        "winner": _determine_winner(result_a, result_b),
        "comparison": _build_comparison(result_a, result_b),
    }
    return comparison


def _determine_winner(a: AuditResult, b: AuditResult) -> Dict[str, str]:
    """Determine winner for each dimension."""
    winners = {}

    # Overall score
    if a.score > b.score:
        winners["overall"] = a.url
    elif b.score > a.score:
        winners["overall"] = b.url
    else:
        winners["overall"] = "tie"

    # Load time
    if a.load_time < b.load_time:
        winners["speed"] = a.url
    elif b.load_time < a.load_time:
        winners["speed"] = b.url
    else:
        winners["speed"] = "tie"

    # Error count
    if len(a.errors) < len(b.errors):
        winners["errors"] = a.url
    elif len(b.errors) < len(a.errors):
        winners["errors"] = b.url
    else:
        winners["errors"] = "tie"

    return winners


def _build_comparison(a: AuditResult, b: AuditResult) -> list:
    """Build comparison table."""
    rows = [
        _cmp_row("Overall Score", a.score, b.score, higher_better=True),
        _cmp_row("Grade", a.grade, b.grade),
        _cmp_row("Load Time (s)", a.load_time, b.load_time, higher_better=False),
        _cmp_row("Page Size (KB)",
                  a.details.get("page_size_kb", 0),
                  b.details.get("page_size_kb", 0),
                  higher_better=False),
        _cmp_row("Errors", len(a.errors), len(b.errors), higher_better=False),
        _cmp_row("Warnings", len(a.warnings), len(b.warnings), higher_better=False),
        _cmp_row("Passed Checks", len(a.passed), len(b.passed), higher_better=True),
        _cmp_row("Internal Links",
                  a.details.get("internal_links", 0),
                  b.details.get("internal_links", 0),
                  higher_better=True),
        _cmp_row("External Links",
                  a.details.get("external_links", 0),
                  b.details.get("external_links", 0)),
        _cmp_row("Has HTTPS",
                  a.url.startswith("https"),
                  b.url.startswith("https")),
        _cmp_row("Has Sitemap",
                  a.details.get("sitemap", False),
                  b.details.get("sitemap", False)),
        _cmp_row("Security Headers (present)",
                  len(a.details.get("security_headers", {}).get("present", [])),
                  len(b.details.get("security_headers", {}).get("present", [])),
                  higher_better=True),
    ]
    return rows


def _cmp_row(label: str, val_a, val_b, higher_better: bool = None) -> dict:
    """Build a single comparison row."""
    row = {"label": label, "site_a": val_a, "site_b": val_b}

    if higher_better is not None and isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
        if higher_better:
            if val_a > val_b:
                row["winner"] = "a"
            elif val_b > val_a:
                row["winner"] = "b"
            else:
                row["winner"] = "tie"
        else:
            if val_a < val_b:
                row["winner"] = "a"
            elif val_b < val_a:
                row["winner"] = "b"
            else:
                row["winner"] = "tie"
    else:
        row["winner"] = "tie"

    return row


def format_comparison_text(comparison: Dict[str, Any]) -> str:
    """Format comparison as human-readable text."""
    a = comparison["site_a"]
    b = comparison["site_b"]
    winners = comparison["winner"]

    lines = [
        "=" * 60,
        "  🔍 SEO Competitor Comparison",
        "=" * 60,
        f"  Site A: {a['url']}",
        f"  Site B: {b['url']}",
        "-" * 60,
        f"  {'Metric':<25} {'Site A':>10} {'Site B':>10} {'Winner':>8}",
        "-" * 60,
    ]

    for row in comparison.get("comparison", []):
        w = {"a": "◄ A", "b": "B ►", "tie": "="}.get(row.get("winner", "tie"), "=")
        lines.append(f"  {row['label']:<25} {str(row['site_a']):>10} {str(row['site_b']):>10} {w:>8}")

    lines.append("-" * 60)
    overall = winners.get("overall", "tie")
    if overall == "tie":
        lines.append("  🏆 Overall: TIE!")
    else:
        lines.append(f"  🏆 Overall Winner: {overall}")
    lines.append("=" * 60)

    return "\n".join(lines)
