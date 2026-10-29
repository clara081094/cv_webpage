from app.api.helpers import created, get_or_404, no_content, ok
from app.errors import ApiError, ConflictError
from app.extensions import db, limiter
from app.models import BeyondItem, Bio, Education, Experience, MediaAsset, Project
from app.schemas.output import dump_media
from app.services import storage
from flask import Blueprint, current_app, request, send_from_directory
from flask_jwt_extended import jwt_required
from sqlalchemy import select

bp = Blueprint("media", __name__)

# (model, column) pairs holding a direct reference to an asset.
COVER_REFERENCES = (
    (Bio, "photo_id"),
    (Education, "logo_id"),
    (Experience, "logo_id"),
    (Project, "cover_id"),
    (BeyondItem, "cover_id"),
)

# Models whose JSONB `images` column can embed an asset.
GALLERY_MODELS = (Project, BeyondItem)


@bp.get("/files/<path:filename>")
def serve_file(filename):
    """Dev convenience: in production nginx serves this path directly."""
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@bp.get("/admin/media")
@jwt_required()
def list_media():
    assets = db.session.scalars(
        select(MediaAsset).order_by(MediaAsset.uploaded_at.desc())
    ).all()
    return ok([dump_media(asset) for asset in assets])


@bp.post("/admin/media")
@jwt_required()
@limiter.limit("20 per hour")
def upload_media():
    if "file" not in request.files:
        raise ApiError("Send the image as multipart field 'file'", code="MISSING_FILE")

    info = storage.save_upload(request.files["file"])

    # Same bytes uploaded twice: reuse the row, drop the duplicate file.
    existing = db.session.scalars(
        select(MediaAsset).where(MediaAsset.checksum_sha256 == info["checksum_sha256"])
    ).first()
    if existing is not None:
        storage.delete_file(info["filename"])
        return ok(dump_media(existing))

    asset = MediaAsset(**info, alt_text=request.form.get("alt_text"))
    db.session.add(asset)
    db.session.commit()
    return created(dump_media(asset))


@bp.patch("/admin/media/<uuid:media_id>")
@jwt_required()
def update_media(media_id):
    asset = get_or_404(MediaAsset, media_id)
    asset.alt_text = (request.get_json(silent=True) or {}).get("alt_text")
    db.session.commit()
    return ok(dump_media(asset))


@bp.delete("/admin/media/<uuid:media_id>")
@jwt_required()
def delete_media(media_id):
    asset = get_or_404(MediaAsset, media_id)

    for model, column in COVER_REFERENCES:
        used = db.session.scalars(
            select(model.id).where(getattr(model, column) == asset.id).limit(1)
        ).first()
        if used is not None:
            raise ConflictError(
                "Media is still referenced; detach it first",
                details={"referenced_by": model.__tablename__},
            )

    for model in GALLERY_MODELS:
        used = db.session.scalars(
            select(model.id)
            .where(model.images.contains([{"media_id": str(asset.id)}]))
            .limit(1)
        ).first()
        if used is not None:
            raise ConflictError(
                "Media is used in a gallery; remove it from the gallery first",
                details={"referenced_by": f"{model.__tablename__}.images"},
            )

    filename = asset.filename
    db.session.delete(asset)
    db.session.commit()
    storage.delete_file(filename)
    return no_content()
