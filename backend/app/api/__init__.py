"""Blueprint registration.

The public API is split by section of the site — about / projects / beyond —
which is also how the frontend pages are split.
"""

from app.api import about, admin, auth, beyond, health, media, projects


def register_blueprints(app) -> None:
    prefix = app.config["API_PREFIX"]

    app.register_blueprint(health.bp, url_prefix=prefix)

    # public, one blueprint per section
    app.register_blueprint(about.bp, url_prefix=prefix)
    app.register_blueprint(projects.bp, url_prefix=prefix)
    app.register_blueprint(beyond.bp, url_prefix=prefix)

    app.register_blueprint(auth.bp, url_prefix=f"{prefix}/auth")
    app.register_blueprint(media.bp, url_prefix=prefix)
    app.register_blueprint(admin.bp, url_prefix=f"{prefix}/admin")
