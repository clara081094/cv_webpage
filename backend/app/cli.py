import click
from app.extensions import db
from flask.cli import AppGroup
from sqlalchemy import select, text


def register_cli(app) -> None:
    users_cli = AppGroup("users", help="Admin user management.")

    @app.cli.command("seed-all")
    def seed_all():
        """Load DEMO content (idempotent). Optional: a fresh deploy starts empty."""
        from seeds import seed_initial

        seed_initial.run()
        click.echo(
            "seeded: bio, social links, experience, education, languages, "
            "projects, beyond"
        )

    @app.cli.command("db-init-extensions")
    def db_init_extensions():
        """Enable the Postgres extensions the schema depends on."""
        db.session.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        db.session.commit()
        click.echo("pgcrypto ready")

    @app.cli.command("db-reset")
    def db_reset():
        """Drop and recreate every table. Development only."""
        if not app.config.get("DEBUG") and not app.config.get("TESTING"):
            raise click.ClickException("db-reset is blocked outside development")
        click.confirm("This deletes ALL data. Continue?", abort=True)
        db.drop_all()
        db.session.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        db.session.commit()
        db.create_all()
        click.echo("schema recreated")

    @users_cli.command("create-admin")
    @click.option("--email", prompt=True)
    @click.option("--full-name", default=None)
    @click.password_option()
    def create_admin(email, full_name, password):
        """Create the admin account used to log into the API."""
        from app.models import AdminUser

        email = email.strip().lower()
        if len(password) < 8:
            raise click.ClickException("password must be at least 8 characters")
        if db.session.scalars(
            select(AdminUser).where(AdminUser.email == email)
        ).first():
            raise click.ClickException(f"{email} already exists")
        user = AdminUser(email=email, full_name=full_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"admin created: {email}")

    @users_cli.command("set-password")
    @click.option("--email", prompt=True)
    @click.password_option()
    def set_password(email, password):
        """Reset an admin password."""
        from app.models import AdminUser

        user = db.session.scalars(
            select(AdminUser).where(AdminUser.email == email.strip().lower())
        ).first()
        if user is None:
            raise click.ClickException(f"{email} not found")
        user.set_password(password)
        db.session.commit()
        click.echo("password updated")

    @app.cli.command("routes-json")
    def routes_json():
        """List every route: handy to keep the README endpoint table honest."""
        for rule in sorted(app.url_map.iter_rules(), key=lambda r: str(r)):
            methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
            click.echo(f"{methods:24} {rule}")

    app.cli.add_command(users_cli)
