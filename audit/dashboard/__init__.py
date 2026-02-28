"""
审计仪表盘 - FastAPI
"""

import time
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

dashboard_app = FastAPI(title="SEO Audit Dashboard", version="3.0.0")

_history = None


def setup_dashboard(history):
    global _history
    _history = history


@dashboard_app.get("/", response_class=HTMLResponse)
async def index():
    """仪表盘首页"""
    if not _history:
        return HTMLResponse("<h1>Dashboard not configured</h1>", status_code=503)

    domains = _history.get_domains()
    domain_cards = ""
    for domain in domains:
        records = _history.get_history(domain, limit=1)
        if records:
            latest = records[0]
            color = "#4caf50" if latest.score >= 80 else "#ff9800" if latest.score >= 60 else "#f44336"
            domain_cards += f"""
            <div class='card'>
                <h3>{domain}</h3>
                <div class='score' style='color:{color}'>{latest.score}</div>
                <p>Grade: {latest.grade} | Errors: {latest.errors} | Warnings: {latest.warnings}</p>
                <p><small>{latest.created_at}</small></p>
                <a href='/api/history?domain={domain}'>View History →</a>
            </div>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>SEO Audit Dashboard</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
h1 {{ color: #333; }} .card {{ background: white; padding: 16px; margin: 10px 0; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.score {{ font-size: 48px; font-weight: bold; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
a {{ color: #1976d2; }}
</style></head><body>
<h1>📊 SEO Audit Dashboard</h1>
<p>Monitoring {len(domains)} domain(s) | Total audits: {_history.count()}</p>
<div class='grid'>{domain_cards}</div>
</body></html>"""
    return HTMLResponse(html)


@dashboard_app.get("/api/history")
async def api_history(
    domain: str = Query(...),
    limit: int = Query(30, ge=1, le=100),
):
    """获取域名审计历史"""
    if not _history:
        raise HTTPException(503, "History not configured")
    records = _history.get_history(domain, limit)
    return [
        {
            "id": r.id,
            "score": r.score,
            "grade": r.grade,
            "errors": r.errors,
            "warnings": r.warnings,
            "load_time": r.load_time,
            "created_at": r.created_at,
        }
        for r in records
    ]


@dashboard_app.get("/api/trend")
async def api_trend(
    domain: str = Query(...),
    days: int = Query(30, ge=1, le=365),
):
    """获取分数趋势"""
    if not _history:
        raise HTTPException(503, "History not configured")
    return _history.get_trend(domain, days)


@dashboard_app.get("/api/domains")
async def api_domains():
    """列出所有域名"""
    if not _history:
        raise HTTPException(503, "History not configured")
    domains = _history.get_domains()
    result = []
    for d in domains:
        records = _history.get_history(d, limit=1)
        result.append({
            "domain": d,
            "latest_score": records[0].score if records else 0,
            "total_audits": _history.count(d),
        })
    return result
