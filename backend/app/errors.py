import logging

from flask import jsonify
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """Raised by the API layer to produce a predictable error envelope."""

    status_code = 400
    code = "BAD_REQUEST"

    def __init__(self, message, *, code=None, status_code=None, details=None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        self.details = details or {}


class NotFoundError(ApiError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(ApiError):
    status_code = 409
    code = "CONFLICT"


class ValidationApiError(ApiError):
    status_code = 422
    code = "VALIDATION_ERROR"


def _envelope(code, message, details=None, status=400):
    payload = {"error": {"code": code, "message": message, "details": details or {}}}
    return jsonify(payload), status


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(exc: ApiError):
        return _envelope(exc.code, exc.message, exc.details, exc.status_code)

    @app.errorhandler(ValidationError)
    def handle_pydantic_error(exc: ValidationError):
        details = {
            ".".join(str(part) for part in err["loc"]): err["msg"]
            for err in exc.errors()
        }
        return _envelope("VALIDATION_ERROR", "Payload validation failed", details, 422)

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(exc: IntegrityError):
        from app.extensions import db

        db.session.rollback()
        logger.warning("integrity error: %s", exc.orig)
        return _envelope(
            "CONFLICT",
            "The request conflicts with existing data (duplicate or missing reference)",
            {},
            409,
        )

    @app.errorhandler(HTTPException)
    def handle_http_error(exc: HTTPException):
        code = exc.name.upper().replace(" ", "_")
        return _envelope(code, exc.description, {}, exc.code or 500)

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        logger.exception("unhandled error")
        if app.config.get("DEBUG") or app.config.get("TESTING"):
            raise exc
        return _envelope("INTERNAL_ERROR", "Unexpected server error", {}, 500)
