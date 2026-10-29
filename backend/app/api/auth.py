from datetime import UTC, datetime

from app.api.helpers import body, ok
from app.errors import ApiError
from app.extensions import db, limiter
from app.models import AdminUser, TokenBlocklist
from app.schemas.output import dump_user
from app.schemas.payloads import LoginIn
from flask import Blueprint, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    current_user,
    get_jwt,
    jwt_required,
)
from sqlalchemy import select

bp = Blueprint("auth", __name__)


@bp.post("/login")
@limiter.limit("5 per minute")
def login():
    payload = LoginIn.model_validate(body())
    user = db.session.scalars(
        select(AdminUser).where(AdminUser.email == payload.email.lower())
    ).first()

    # Same message for unknown email and wrong password: no user enumeration.
    if user is None or not user.check_password(payload.password) or not user.is_active:
        raise ApiError(
            "Invalid credentials", code="INVALID_CREDENTIALS", status_code=401
        )

    user.last_login_at = datetime.now(UTC)
    db.session.commit()

    identity = str(user.id)
    return jsonify(
        {
            "access_token": create_access_token(identity=identity),
            "refresh_token": create_refresh_token(identity=identity),
            "user": dump_user(user),
        }
    )


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    return jsonify({"access_token": create_access_token(identity=str(current_user.id))})


@bp.post("/logout")
@jwt_required(verify_type=False)
def logout():
    claims = get_jwt()
    expires_at = datetime.fromtimestamp(claims["exp"], tz=UTC)
    db.session.add(
        TokenBlocklist(
            jti=claims["jti"], token_type=claims["type"], expires_at=expires_at
        )
    )
    db.session.commit()
    return jsonify({"data": {"revoked": claims["type"]}})


@bp.get("/me")
@jwt_required()
def me():
    return ok(dump_user(current_user))
