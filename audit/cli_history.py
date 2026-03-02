"""
CLI commands for history tracking
"""
import click
from audit.checks.history import HistoryTracker
from tabulate import tabulate


@click.group()
def history():
    """SEO audit history tracking commands"""
    pass


@history.command()
@click.argument('url')
@click.option('--limit', default=10, help='Number of audits to show')
@click.option('--db', default='seo_history.db', help='Database path')
def show(url, limit, db):
    """Show audit history for a URL"""
    tracker = HistoryTracker(db_path=db)
    history_data = tracker.get_history(url, limit=limit)
    
    if not history_data:
        click.echo(f"No history found for {url}")
        return
    
    table_data = [
        [
            h["id"],
            h["timestamp"][:19],
            h["score"],
            h["issues_count"]
        ]
        for h in history_data
    ]
    
    click.echo(f"\n📊 Audit History: {url}\n")
    click.echo(tabulate(
        table_data,
        headers=["ID", "Timestamp", "Score", "Issues"],
        tablefmt="grid"
    ))


@history.command()
@click.argument('url')
@click.option('--days', default=30, help='Number of days to analyze')
@click.option('--db', default='seo_history.db', help='Database path')
def trend(url, days, db):
    """Show trend analysis for a URL"""
    tracker = HistoryTracker(db_path=db)
    trend_data = tracker.get_trend(url, days=days)
    
    if "error" in trend_data:
        click.echo(f"❌ {trend_data['error']}")
        return
    
    click.echo(f"\n📈 Trend Analysis: {url} (last {days} days)\n")
    click.echo(f"Total audits: {trend_data['audits_count']}")
    
    score_trend = trend_data['score_trend']
    click.echo(f"\n🎯 Score Trend:")
    click.echo(f"  First: {score_trend['first']}")
    click.echo(f"  Last:  {score_trend['last']}")
    click.echo(f"  Change: {score_trend['change']:+d}")
    click.echo(f"  Average: {score_trend['avg']:.1f}")
    click.echo(f"  Range: {score_trend['min']} - {score_trend['max']}")
    
    issues_trend = trend_data['issues_trend']
    click.echo(f"\n🐛 Issues Trend:")
    click.echo(f"  First: {issues_trend['first']}")
    click.echo(f"  Last:  {issues_trend['last']}")
    click.echo(f"  Change: {issues_trend['change']:+d}")
    click.echo(f"  Average: {issues_trend['avg']:.1f}")


@history.command()
@click.argument('url')
@click.argument('audit_id', type=int)
@click.option('--db', default='seo_history.db', help='Database path')
def detail(url, audit_id, db):
    """Show detailed audit result"""
    tracker = HistoryTracker(db_path=db)
    history_data = tracker.get_history(url, limit=100)
    
    audit = next((h for h in history_data if h["id"] == audit_id), None)
    
    if not audit:
        click.echo(f"❌ Audit #{audit_id} not found for {url}")
        return
    
    click.echo(f"\n📋 Audit #{audit_id} Details\n")
    click.echo(f"URL: {url}")
    click.echo(f"Timestamp: {audit['timestamp']}")
    click.echo(f"Score: {audit['score']}")
    click.echo(f"Issues: {audit['issues_count']}")
    click.echo(f"\nFull data:")
    click.echo(audit['data'])


if __name__ == '__main__':
    history()
