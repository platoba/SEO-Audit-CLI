"""PDF report generator (optional - requires weasyprint or falls back to HTML)."""

import os
from typing import Union, List
from ..core import AuditResult
from .html_report import generate_html_report


def save_pdf_report(results: Union[AuditResult, List[AuditResult]], filepath: str) -> str:
    """Generate PDF report. Requires weasyprint. Falls back to HTML if unavailable."""
    html_content = generate_html_report(results)

    try:
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(filepath)
        return filepath
    except ImportError:
        # Fallback: save as HTML with .pdf.html extension
        fallback_path = filepath.replace(".pdf", ".pdf.html")
        with open(fallback_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return fallback_path
