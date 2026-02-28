"""JSON report generator."""

import json
from typing import Union, List
from ..core import AuditResult


def generate_json_report(results: Union[AuditResult, List[AuditResult]], pretty: bool = True) -> str:
    """Generate JSON report string."""
    if isinstance(results, list):
        data = {
            "report_type": "batch_audit",
            "total_urls": len(results),
            "results": [r.to_dict() for r in results],
            "summary": _batch_summary(results),
        }
    else:
        data = results.to_dict()

    indent = 2 if pretty else None
    return json.dumps(data, indent=indent, ensure_ascii=False)


def save_json_report(results: Union[AuditResult, List[AuditResult]], filepath: str):
    """Save JSON report to file."""
    content = generate_json_report(results)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def _batch_summary(results: List[AuditResult]) -> dict:
    scores = [r.score for r in results]
    return {
        "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "total_errors": sum(len(r.errors) for r in results),
        "total_warnings": sum(len(r.warnings) for r in results),
    }
