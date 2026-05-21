"""Token usage tracker — persistent SQLite-backed counter.

Records per-agent and per-request token consumption. Exposed via /api/stats endpoint.
"""
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional


class TokenTracker:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with self._conn() as c:
            c.execute(
                """CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    timestamp INTEGER NOT NULL
                )"""
            )
            c.execute("CREATE INDEX IF NOT EXISTS idx_request ON usage(request_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_agent ON usage(agent)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_ts ON usage(timestamp)")

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def record(
        self,
        request_id: str,
        agent: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ):
        total = prompt_tokens + completion_tokens
        with self._conn() as c:
            c.execute(
                "INSERT INTO usage (request_id, agent, model, prompt_tokens, completion_tokens, total_tokens, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (request_id, agent, model, prompt_tokens, completion_tokens, total, int(time.time())),
            )

    def get_stats(self, since_seconds: Optional[int] = None) -> dict:
        cutoff = int(time.time() - since_seconds) if since_seconds else 0
        with self._conn() as c:
            cur = c.execute(
                "SELECT agent, SUM(prompt_tokens), SUM(completion_tokens), SUM(total_tokens), COUNT(*) FROM usage WHERE timestamp >= ? GROUP BY agent",
                (cutoff,),
            )
            per_agent = {
                row[0]: {
                    "prompt": row[1] or 0,
                    "completion": row[2] or 0,
                    "total": row[3] or 0,
                    "calls": row[4] or 0,
                }
                for row in cur.fetchall()
            }

            cur = c.execute(
                "SELECT SUM(total_tokens), COUNT(*) FROM usage WHERE timestamp >= ?",
                (cutoff,),
            )
            row = cur.fetchone()
            grand_total = row[0] or 0
            total_calls = row[1] or 0

        return {
            "per_agent": per_agent,
            "grand_total_tokens": grand_total,
            "total_calls": total_calls,
        }

    def get_request_breakdown(self, request_id: str) -> list:
        with self._conn() as c:
            cur = c.execute(
                "SELECT agent, model, prompt_tokens, completion_tokens, total_tokens, timestamp FROM usage WHERE request_id = ? ORDER BY timestamp",
                (request_id,),
            )
            return [
                {
                    "agent": r[0],
                    "model": r[1],
                    "prompt_tokens": r[2],
                    "completion_tokens": r[3],
                    "total_tokens": r[4],
                    "timestamp": r[5],
                }
                for r in cur.fetchall()
            ]
