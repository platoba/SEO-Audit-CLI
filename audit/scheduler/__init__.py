"""
定时审计调度 - SQLite历史存储 + 报警
"""

import time
import json
import sqlite3
import logging
import threading
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AuditRecord:
    """历史审计记录"""
    id: int = 0
    url: str = ""
    domain: str = ""
    score: int = 0
    grade: str = ""
    errors: int = 0
    warnings: int = 0
    load_time: float = 0.0
    details_json: str = "{}"
    created_at: str = ""


class AuditHistory:
    """
    SQLite审计历史存储
    """

    def __init__(self, db_path: str = "audit_history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                domain TEXT NOT NULL,
                score INTEGER DEFAULT 0,
                grade TEXT DEFAULT '',
                errors INTEGER DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                load_time REAL DEFAULT 0.0,
                details_json TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_domain ON audit_history(domain)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_created ON audit_history(created_at)
        """)
        conn.commit()
        conn.close()

    def save(self, result) -> int:
        """保存审计结果"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            """INSERT INTO audit_history (url, domain, score, grade, errors, warnings, load_time, details_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                result.url,
                result.domain,
                result.score,
                result.grade,
                len(result.errors),
                len(result.warnings),
                result.load_time,
                json.dumps(getattr(result, "details", {})),
            ),
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        return row_id

    def get_history(self, domain: str, limit: int = 30) -> List[AuditRecord]:
        """获取域名历史"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT * FROM audit_history WHERE domain = ?
               ORDER BY created_at DESC LIMIT ?""",
            (domain, limit),
        ).fetchall()
        conn.close()
        return [AuditRecord(**dict(r)) for r in rows]

    def get_trend(self, domain: str, days: int = 30) -> List[Dict]:
        """获取分数趋势"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT date(created_at) as date, AVG(score) as avg_score,
                      MIN(score) as min_score, MAX(score) as max_score,
                      COUNT(*) as count
               FROM audit_history
               WHERE domain = ? AND created_at >= datetime('now', ?)
               GROUP BY date(created_at)
               ORDER BY date""",
            (domain, f"-{days} days"),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_domains(self) -> List[str]:
        """获取所有已审计的域名"""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT DISTINCT domain FROM audit_history ORDER BY domain"
        ).fetchall()
        conn.close()
        return [r[0] for r in rows]

    def count(self, domain: Optional[str] = None) -> int:
        """计数"""
        conn = sqlite3.connect(self.db_path)
        if domain:
            row = conn.execute(
                "SELECT COUNT(*) FROM audit_history WHERE domain = ?",
                (domain,),
            ).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) FROM audit_history").fetchone()
        conn.close()
        return row[0]


@dataclass
class AlertConfig:
    """报警配置"""
    score_threshold: int = 70  # 低于此分数报警
    score_drop_threshold: int = 10  # 分数下降超过此值报警
    callback: Optional[Callable] = None  # 报警回调


class AlertChecker:
    """
    分数报警检查器
    """

    def __init__(self, history: AuditHistory, config: AlertConfig):
        self.history = history
        self.config = config

    def check(self, result) -> List[str]:
        """检查是否需要报警"""
        alerts = []

        # 低分报警
        if result.score < self.config.score_threshold:
            alerts.append(
                f"⚠️ Low score: {result.domain} scored {result.score} "
                f"(threshold: {self.config.score_threshold})"
            )

        # 分数下降报警
        history = self.history.get_history(result.domain, limit=1)
        if history:
            last_score = history[0].score
            drop = last_score - result.score
            if drop >= self.config.score_drop_threshold:
                alerts.append(
                    f"📉 Score drop: {result.domain} dropped {drop} points "
                    f"({last_score} → {result.score})"
                )

        # 触发回调
        if alerts and self.config.callback:
            for alert in alerts:
                try:
                    self.config.callback(alert)
                except Exception as e:
                    logger.error(f"Alert callback error: {e}")

        return alerts
