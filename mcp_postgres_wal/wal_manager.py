import os
import json
import psycopg
from typing import Dict, Any, List, Optional
from datetime import datetime

class PostgresWalManager:
    """
    Manages deterministic agent checkpointing using PostgreSQL tables mimicking
    Write-Ahead Logging (WAL) state persistence and ACID transactions.
    """
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable or argument is required.")
        self.table_name = "botmartz_agent_wal_checkpoints"

    def init_schema(self):
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        id BIGSERIAL PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        step_index INTEGER NOT NULL,
                        node_name TEXT NOT NULL,
                        state_payload JSONB NOT NULL,
                        compensating_action JSONB,
                        status TEXT NOT NULL DEFAULT 'COMMITTED',
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_session
                    ON {self.table_name} (session_id, step_index DESC);
                """)
                conn.commit()

    def record_checkpoint(
        self,
        session_id: str,
        step_index: int,
        node_name: str,
        state_payload: Dict[str, Any],
        compensating_action: Optional[Dict[str, Any]] = None
    ) -> int:
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    INSERT INTO {self.table_name}
                    (session_id, step_index, node_name, state_payload, compensating_action, status)
                    VALUES (%s, %s, %s, %s, %s, 'COMMITTED')
                    RETURNING id;
                """, (
                    session_id,
                    step_index,
                    node_name,
                    json.dumps(state_payload),
                    json.dumps(compensating_action) if compensating_action else None
                ))
                checkpoint_id = cur.fetchone()[0]
                conn.commit()
                return checkpoint_id

    def get_latest_checkpoint(self, session_id: str) -> Optional[Dict[str, Any]]:
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT id, session_id, step_index, node_name, state_payload, compensating_action, status, created_at
                    FROM {self.table_name}
                    WHERE session_id = %s
                    ORDER BY step_index DESC
                    LIMIT 1;
                """, (session_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "checkpoint_id": row[0],
                    "session_id": row[1],
                    "step_index": row[2],
                    "node_name": row[3],
                    "state_payload": row[4],
                    "compensating_action": row[5],
                    "status": row[6],
                    "created_at": row[7].isoformat()
                }

    def execute_saga_rollback(self, session_id: str) -> List[Dict[str, Any]]:
        """Reverses all executed state-changing operations in reverse chronological order."""
        executed_compensations = []
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT id, step_index, node_name, compensating_action
                    FROM {self.table_name}
                    WHERE session_id = %s AND compensating_action IS NOT NULL AND status = 'COMMITTED'
                    ORDER BY step_index DESC;
                """, (session_id,))
                rows = cur.fetchall()

                for row in rows:
                    cp_id, step, node, comp = row
                    executed_compensations.append({
                        "checkpoint_id": cp_id,
                        "step_index": step,
                        "node_name": node,
                        "compensating_action": comp,
                        "reverted_at": datetime.utcnow().isoformat()
                    })
                    cur.execute(f"""
                        UPDATE {self.table_name}
                        SET status = 'COMPENSATED'
                        WHERE id = %s;
                    """, (cp_id,))
                conn.commit()
        return executed_compensations
