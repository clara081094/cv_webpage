from app.extensions import db
from flask import Blueprint, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        db_status = "ok"
        status_code = 200
    except SQLAlchemyError as exc:
        db.session.rollback()
        db_status = f"error: {exc.__class__.__name__}"
        status_code = 503
    return (
        jsonify(
            {"status": "ok" if status_code == 200 else "degraded", "db": db_status}
        ),
        status_code,
    )
