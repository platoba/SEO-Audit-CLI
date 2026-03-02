"""
SEO History Tracker - Track SEO metrics over time
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class HistoryTracker:
    """Track and compare SEO audit results over time"""
    
    def __init__(self, db_path: str = "seo_history.db"):
        self.db_path = Path(db_path)
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                score INTEGER,
                issues_count INTEGER,
                data TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_url_timestamp 
            ON audits(url, timestamp DESC)
        """)
        
        conn.commit()
        conn.close()
    
    def save_audit(self, url: str, audit_data: Dict) -> int:
        """Save audit result to history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.utcnow().isoformat()
        score = audit_data.get("score", 0)
        issues_count = sum(len(check.get("issues", [])) 
                          for check in audit_data.get("checks", {}).values())
        
        cursor.execute("""
            INSERT INTO audits (url, timestamp, score, issues_count, data)
            VALUES (?, ?, ?, ?, ?)
        """, (url, timestamp, score, issues_count, json.dumps(audit_data)))
        
        audit_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return audit_id
    
    def get_history(self, url: str, limit: int = 10) -> List[Dict]:
        """Get audit history for a URL"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, score, issues_count, data
            FROM audits
            WHERE url = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (url, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "timestamp": row[1],
                "score": row[2],
                "issues_count": row[3],
                "data": json.loads(row[4])
            })
        
        conn.close()
        return results
    
    def compare_with_previous(self, url: str, current_data: Dict) -> Optional[Dict]:
        """Compare current audit with previous one"""
        history = self.get_history(url, limit=2)
        
        if len(history) < 1:
            return None
        
        previous = history[0]
        
        return {
            "score_change": current_data.get("score", 0) - previous["score"],
            "issues_change": sum(len(check.get("issues", [])) 
                                for check in current_data.get("checks", {}).values()) - previous["issues_count"],
            "previous_timestamp": previous["timestamp"],
            "previous_score": previous["score"],
            "previous_issues": previous["issues_count"]
        }
    
    def get_trend(self, url: str, days: int = 30) -> Dict:
        """Get trend analysis for a URL"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, score, issues_count
            FROM audits
            WHERE url = ?
            AND datetime(timestamp) >= datetime('now', '-' || ? || ' days')
            ORDER BY timestamp ASC
        """, (url, days))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return {"error": "No data available"}
        
        scores = [row[1] for row in rows]
        issues = [row[2] for row in rows]
        
        return {
            "url": url,
            "period_days": days,
            "audits_count": len(rows),
            "score_trend": {
                "first": scores[0],
                "last": scores[-1],
                "change": scores[-1] - scores[0],
                "avg": sum(scores) / len(scores),
                "min": min(scores),
                "max": max(scores)
            },
            "issues_trend": {
                "first": issues[0],
                "last": issues[-1],
                "change": issues[-1] - issues[0],
                "avg": sum(issues) / len(issues),
                "min": min(issues),
                "max": max(issues)
            },
            "timestamps": [row[0] for row in rows]
        }


def check_history(url: str, audit_data: Dict, tracker: Optional[HistoryTracker] = None) -> Dict:
    """History check module for SEO audit"""
    if tracker is None:
        tracker = HistoryTracker()
    
    # Save current audit
    audit_id = tracker.save_audit(url, audit_data)
    
    # Compare with previous
    comparison = tracker.compare_with_previous(url, audit_data)
    
    # Get 30-day trend
    trend = tracker.get_trend(url, days=30)
    
    return {
        "status": "pass",
        "audit_id": audit_id,
        "comparison": comparison,
        "trend": trend,
        "message": "Audit saved to history database"
    }
