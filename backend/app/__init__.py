import importlib
import logging
import uuid

from app.api import register_blueprints
from app.cli import register_cli
from app.config import resolve_config
from app.errors import register_error_handlers
from app.extensions import cors, db, jwt, limiter, migrate
from flask import Flask, g, request
from sqlalchemy import select


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)
    config = resolve_config(config_name)
    if hasattr(config, "check_secrets"):
        config.check_secrets()
    app.config.from_object(config)

    _configure_logging(app)
    _init_extensions(app)
    _configure_jwt(app)

    register_error_handlers(app)
    register_blueprints(app)
    register_cli(app)

    @app.before_request
    def start_request():
        g.request_id = request.headers.get("X-Request-Id", uuid.uuid4().hex[:12])
        # g lives on the app context, which is reused when one is already
        # pushed (tests, CLI). Clear the per-request i18n flag explicitly.
        g.pop("lang_fallback", None)

    @app.after_request
    def echo_request_id(response):
        response.headers["X-Request-Id"] = getattr(g, "request_id", "-")
        return response

    return app


def _init_extensions(app: Flask) -> None:
    # Import side effect: register every mapper before create_all/migrations run.
    # importlib avoids `import app.models` shadowing the `app` argument.
    importlib.import_module("app.models")

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
        expose_headers=["X-Request-Id"],
    )


def _configure_logging(app: Flask) -> None:
    level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO
    logging.basicConfig(
        level=level,
        format='{"level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
    )
    app.logger.setLevel(level)


def _configure_jwt(app: Flask) -> None:
    from app.models import AdminUser, TokenBlocklist

    @jwt.user_lookup_loader
    def load_user(_jwt_header, jwt_data):
        return db.session.get(AdminUser, uuid.UUID(jwt_data["sub"]))

    @jwt.token_in_blocklist_loader
    def is_revoked(_jwt_header, jwt_data):
        jti = jwt_data["jti"]
        return (
            db.session.scalars(
                select(TokenBlocklist.id).where(TokenBlocklist.jti == jti)
            ).first()
            is not None
        )

    @jwt.unauthorized_loader
    def missing_token(reason):
        return {
            "error": {"code": "UNAUTHORIZED", "message": reason, "details": {}}
        }, 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return {
            "error": {"code": "INVALID_TOKEN", "message": reason, "details": {}}
        }, 401

    @jwt.expired_token_loader
    def expired_token(_header, _payload):
        return {
            "error": {
                "code": "TOKEN_EXPIRED",
                "message": "Token has expired",
                "details": {},
            }
        }, 401

    @jwt.revoked_token_loader
    def revoked_token(_header, _payload):
        return {
            "error": {
                "code": "TOKEN_REVOKED",
                "message": "Token has been revoked",
                "details": {},
            }
        }, 401
