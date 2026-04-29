from flask import Flask
from .extensions import db, migrate

def create_app(config_object="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.fis import fis_bp
    from app.routes.kartlar import kartlar_bp
    from app.routes.stoklar import stoklar_bp
    from app.routes.raporlar import raporlar_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(fis_bp)
    app.register_blueprint(kartlar_bp)
    app.register_blueprint(stoklar_bp)
    app.register_blueprint(raporlar_bp)

    return app
