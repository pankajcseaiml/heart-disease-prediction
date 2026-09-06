"""Database schema and data access operations for predictions."""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    risk_percentage REAL NOT NULL,
    risk_category TEXT NOT NULL,
    confidence REAL NOT NULL,
    clinical_score REAL NOT NULL,
    image_score REAL NOT NULL,
    fusion_score REAL NOT NULL,
    explanation TEXT NOT NULL,
    normalized_inputs JSON NOT NULL,
    feature_importance JSON NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_risk_category ON predictions(risk_category);
"""


def init_tables(conn: sqlite3.Connection) -> None:
    """Creates tables and indexes if they do not exist."""
    conn.executescript(SCHEMA_SQL)


def save_prediction(
    conn: sqlite3.Connection,
    risk_percentage: float,
    risk_category: str,
    confidence: float,
    clinical_score: float,
    image_score: float,
    fusion_score: float,
    explanation: str,
    normalized_inputs: Dict[str, float],
    feature_importance: List[Dict[str, Any]],
) -> int:
    """Inserts a prediction audit record and returns its ID."""
    created_at = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        """
        INSERT INTO predictions (
            created_at, risk_percentage, risk_category, confidence,
            clinical_score, image_score, fusion_score, explanation,
            normalized_inputs, feature_importance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            created_at,
            risk_percentage,
            risk_category,
            confidence,
            clinical_score,
            image_score,
            fusion_score,
            explanation,
            json.dumps(normalized_inputs),
            json.dumps(feature_importance),
        ),
    )
    return cursor.lastrowid or 0


def get_recent_predictions(conn: sqlite3.Connection, limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieves recent predictions for auditing and history."""
    cursor = conn.execute(
        """
        SELECT id, created_at, risk_percentage, risk_category, confidence,
               clinical_score, image_score, fusion_score, explanation,
               normalized_inputs, feature_importance
        FROM predictions
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "created_at": r["created_at"],
            "risk_percentage": r["risk_percentage"],
            "risk_category": r["risk_category"],
            "confidence": r["confidence"],
            "clinical_score": r["clinical_score"],
            "image_score": r["image_score"],
            "fusion_score": r["fusion_score"],
            "explanation": r["explanation"],
            "normalized_inputs": json.loads(r["normalized_inputs"]),
            "feature_importance": json.loads(r["feature_importance"]),
        })
    return results


def get_prediction_count(conn: sqlite3.Connection) -> int:
    cursor = conn.execute("SELECT COUNT(*) FROM predictions;")
    return cursor.fetchone()[0]
