"""HTML report generator."""

import os
from typing import Union, List
from ..core import AuditResult


def generate_html_report(results: Union[AuditResult, List[AuditResult]]) -> str:
    """Generate HTML report string."""
    if isinstance(results, list):
        return _generate_batch_html(results)
    return _generate_single_html(results)


def save_html_report(results: Union[AuditResult, List[AuditResult]], filepath: str):
    """Save HTML report to file."""
    content = generate_html_report(results)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def _score_color(score: int) -> str:
    if score >= 80:
        return "#22c55e"
    elif score >= 60:
        return "#eab308"
    return "#ef4444"


def _severity_icon(severity: str) -> str:
    return {"error": "❌", "warning": "⚠️", "pass": "✅", "info": "ℹ️"}.get(severity, "•")


def _severity_class(severity: str) -> str:
    return {"error": "error", "warning": "warning", "pass": "pass", "info": "info"}.get(severity, "")


def _generate_single_html(result: AuditResult) -> str:
    issues_html = ""
    for issue in result.issues:
        icon = _severity_icon(issue.severity)
        cls = _severity_class(issue.severity)
        issues_html += f'<div class="issue {cls}"><span class="icon">{icon}</span> <span class="cat">[{issue.category}]</span> {issue.message}</div>\n'

    score_color = _score_color(result.score)
    cwv = result.details.get("core_web_vitals", {})
    cwv_html = ""
    if cwv:
        for metric, data in cwv.items():
            status = data.get("status", "unknown")
            status_color = {"good": "#22c55e", "needs_improvement": "#eab308", "poor": "#ef4444"}.get(status, "#888")
            detail_text = ", ".join(f"{k}: {v}" for k, v in data.items() if k != "status")
            cwv_html += f'<div class="cwv-metric"><span class="cwv-dot" style="background:{status_color}"></span> <strong>{metric}</strong>: {status} ({detail_text})</div>\n'

    sec_headers = result.details.get("security_headers", {})
    sec_html = ""
    if sec_headers:
        for h in sec_headers.get("present", []):
            sec_html += f'<span class="badge badge-pass">{h}</span> '
        for h in sec_headers.get("missing", []):
            sec_html += f'<span class="badge badge-warn">{h}</span> '

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SEO Audit Report - {result.url}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#0f172a; color:#e2e8f0; padding:2rem; }}
.container {{ max-width:900px; margin:0 auto; }}
.header {{ text-align:center; margin-bottom:2rem; }}
.header h1 {{ font-size:1.5rem; color:#f8fafc; margin-bottom:0.5rem; }}
.header .url {{ color:#94a3b8; font-size:0.9rem; word-break:break-all; }}
.score-ring {{ width:120px; height:120px; margin:1.5rem auto; position:relative; }}
.score-ring svg {{ transform: rotate(-90deg); }}
.score-ring .value {{ position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); font-size:2rem; font-weight:bold; }}
.grade {{ font-size:1rem; color:#94a3b8; text-align:center; margin-bottom:1rem; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(150px,1fr)); gap:1rem; margin-bottom:2rem; }}
.stat {{ background:#1e293b; border-radius:8px; padding:1rem; text-align:center; }}
.stat .num {{ font-size:1.5rem; font-weight:bold; }}
.stat .label {{ font-size:0.8rem; color:#94a3b8; }}
.section {{ background:#1e293b; border-radius:8px; padding:1.5rem; margin-bottom:1rem; }}
.section h2 {{ font-size:1.1rem; margin-bottom:1rem; color:#f8fafc; }}
.issue {{ padding:0.5rem 0; border-bottom:1px solid #334155; display:flex; align-items:flex-start; gap:0.5rem; font-size:0.9rem; }}
.issue:last-child {{ border-bottom:none; }}
.issue .cat {{ color:#64748b; font-size:0.8rem; }}
.issue.error {{ color:#fca5a5; }}
.issue.warning {{ color:#fde68a; }}
.issue.pass {{ color:#86efac; }}
.issue.info {{ color:#93c5fd; }}
.badge {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:0.75rem; margin:2px; }}
.badge-pass {{ background:#166534; color:#86efac; }}
.badge-warn {{ background:#713f12; color:#fde68a; }}
.cwv-metric {{ padding:0.4rem 0; display:flex; align-items:center; gap:0.5rem; }}
.cwv-dot {{ width:10px; height:10px; border-radius:50%; display:inline-block; }}
.footer {{ text-align:center; color:#475569; font-size:0.8rem; margin-top:2rem; }}
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>🔍 SEO Audit Report</h1>
<div class="url">{result.url}</div>
</div>

<div class="score-ring">
<svg width="120" height="120" viewBox="0 0 120 120">
<circle cx="60" cy="60" r="50" fill="none" stroke="#334155" stroke-width="8"/>
<circle cx="60" cy="60" r="50" fill="none" stroke="{score_color}" stroke-width="8"
  stroke-dasharray="{result.score * 3.14} 314" stroke-linecap="round"/>
</svg>
<div class="value" style="color:{score_color}">{result.score}</div>
</div>
<div class="grade">Grade: {result.grade} | {result.timestamp[:10]}</div>

<div class="stats">
<div class="stat"><div class="num" style="color:#ef4444">{len(result.errors)}</div><div class="label">Errors</div></div>
<div class="stat"><div class="num" style="color:#eab308">{len(result.warnings)}</div><div class="label">Warnings</div></div>
<div class="stat"><div class="num" style="color:#22c55e">{len(result.passed)}</div><div class="label">Passed</div></div>
<div class="stat"><div class="num">{result.load_time}s</div><div class="label">Load Time</div></div>
</div>

{'<div class="section"><h2>📊 Core Web Vitals</h2>' + cwv_html + '</div>' if cwv_html else ''}

{'<div class="section"><h2>🔒 Security Headers</h2>' + sec_html + '</div>' if sec_html else ''}

<div class="section">
<h2>📋 All Findings ({len(result.issues)})</h2>
{issues_html}
</div>

<div class="footer">Generated by SEO-Audit-CLI v2.0 | <a href="https://github.com/platoba/SEO-Audit-CLI" style="color:#3b82f6">GitHub</a></div>
</div>
</body>
</html>"""


def _generate_batch_html(results: List[AuditResult]) -> str:
    scores = [r.score for r in results]
    avg = round(sum(scores) / len(scores), 1) if scores else 0

    rows = ""
    for r in results:
        color = _score_color(r.score)
        rows += f"""<tr>
<td><a href="{r.url}" style="color:#3b82f6">{r.url[:60]}</a></td>
<td style="color:{color}; font-weight:bold">{r.score} ({r.grade})</td>
<td style="color:#ef4444">{len(r.errors)}</td>
<td style="color:#eab308">{len(r.warnings)}</td>
<td>{r.load_time}s</td>
</tr>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Batch SEO Audit Report</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#0f172a; color:#e2e8f0; padding:2rem; }}
.container {{ max-width:1100px; margin:0 auto; }}
h1 {{ text-align:center; margin-bottom:0.5rem; }}
.summary {{ text-align:center; color:#94a3b8; margin-bottom:2rem; }}
table {{ width:100%; border-collapse:collapse; background:#1e293b; border-radius:8px; overflow:hidden; }}
th, td {{ padding:0.75rem 1rem; text-align:left; border-bottom:1px solid #334155; }}
th {{ background:#0f172a; color:#94a3b8; font-size:0.85rem; text-transform:uppercase; }}
tr:hover {{ background:#334155; }}
.footer {{ text-align:center; color:#475569; font-size:0.8rem; margin-top:2rem; }}
</style>
</head>
<body>
<div class="container">
<h1>🔍 Batch SEO Audit Report</h1>
<div class="summary">{len(results)} URLs | Avg Score: {avg}</div>
<table>
<thead><tr><th>URL</th><th>Score</th><th>Errors</th><th>Warnings</th><th>Load Time</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<div class="footer">Generated by SEO-Audit-CLI v2.0</div>
</div>
</body>
</html>"""
