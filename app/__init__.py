# app/__init__.py
from flask import Flask, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Asegurar que existe el directorio de uploads
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # RUTA RAÍZ - Redirección automática
    @app.route('/')
    def index():
        # Si el usuario ya está autenticado, redirigir a contratos
        if current_user.is_authenticated:
            return redirect(url_for('contracts.index'))
        # Si no está autenticado, redirigir a login
        return redirect(url_for('auth.login'))

    # Registrar blueprints
    from app.routes.auth import auth as auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.contracts import contracts as contracts_bp
    app.register_blueprint(contracts_bp)

    from app.routes.notifications import notifications as notifications_bp
    app.register_blueprint(notifications_bp)

    from app.routes.documents import documents as documents_bp
    app.register_blueprint(documents_bp)

    # Manejador de errores 404
    @app.errorhandler(404)
    def page_not_found(e):
        return redirect(url_for('auth.login'))

    return app