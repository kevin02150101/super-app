import os
from flask import Flask, jsonify, render_template, redirect, url_for, request
from flask_login import current_user

from config import Config
from extensions import db, login_manager, csrf, limiter
from errors import MyCamError


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login_page"
    csrf.init_app(app)
    limiter.init_app(app)

    # CSRF: exempt JSON API that we'll protect via header token
    # (CSRF token is still sent through X-CSRFToken header by axios)
    from models.user import User  # noqa

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def _unauth():
        if request.path.startswith("/api/"):
            return jsonify(ok=False, error={"code": "UNAUTHORIZED", "message": "Not signed in"}), 401
        return redirect(url_for("auth.login_page"))

    # Blueprints — MVC
    from controllers.home_controller import bp as home_bp
    from controllers.auth_controller import bp as auth_bp
    from controllers.dashboard_controller import bp as dashboard_bp
    from controllers.capture_controller import bp as capture_bp
    from controllers.history_controller import bp as history_bp
    from controllers.stats_controller import bp as stats_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(capture_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(stats_bp)

    # Blueprints — Web API
    from api.auth_api import bp as auth_api_bp
    from api.analyze_api import bp as analyze_api_bp
    from api.analysis_api import bp as analysis_api_bp
    from api.stats_api import bp as stats_api_bp

    app.register_blueprint(auth_api_bp)
    app.register_blueprint(analyze_api_bp)
    app.register_blueprint(analysis_api_bp)
    app.register_blueprint(stats_api_bp)

    # Error handlers
    @app.errorhandler(MyCamError)
    def handle_mycam_error(e: MyCamError):
        if request.path.startswith("/api/"):
            return jsonify(ok=False, error=e.to_dict()), e.http_status
        return render_template("errors/generic.html", error=e), e.http_status

    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith("/api/"):
            return jsonify(ok=False, error={"code": "NOT_FOUND", "message": "Resource not found"}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def handle_413(e):
        if request.path.startswith("/api/"):
            return jsonify(ok=False, error={"code": "TOO_LARGE", "message": "File too large"}), 413
        return render_template("errors/generic.html",
                               error=MyCamError("TOO_LARGE", "File too large", 413)), 413

    @app.errorhandler(500)
    def handle_500(e):
        if request.path.startswith("/api/"):
            return jsonify(ok=False, error={"code": "SERVER_ERROR", "message": "Server error"}), 500
        return render_template("errors/500.html"), 500

    @app.errorhandler(Exception)
    def handle_uncaught(e):
        # Already a MyCamError / HTTPException — handled by its own handler
        from werkzeug.exceptions import HTTPException
        if isinstance(e, (MyCamError, HTTPException)):
            raise e
        import traceback
        traceback.print_exc()
        app.logger.exception("Unhandled exception: %s", e)
        if request.path.startswith("/api/"):
            return jsonify(ok=False, error={
                "code": "SERVER_ERROR",
                "message": f"{type(e).__name__}: {e}"
            }), 500
        return render_template("errors/500.html"), 500

    # Auto create tables on first run
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=5000, debug=True)
