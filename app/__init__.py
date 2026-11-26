import os
from flask import Flask
from config import Config
from app.extensions import db, bcrypt, login_manager, csrf
from app.models import Usuario
from app.seed import init_db_command, seed_command, criar_admin_command, seed_historico_command

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Garante que a pasta instance exista para o SQLite
    os.makedirs(app.instance_path, exist_ok=True)

    # Inicializa extensões
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configurações do Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Faça login para acessar esta página.'
    login_manager.login_message_category = 'aviso'

    @login_manager.user_loader
    def load_user(user_id):
        db.session.expire_all()
        usuario = db.session.get(Usuario, int(user_id))
        if usuario and not usuario.is_active:
            return None
        return usuario

    @app.before_request
    def verificar_usuario_ativo():
        from flask_login import current_user, logout_user
        if current_user.is_authenticated and not current_user.is_active:
            logout_user()

    # Registra Blueprints
    from app.auth import auth_bp
    from app.main import main_bp
    from app.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    # Registra comandos CLI
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_command)
    app.cli.add_command(criar_admin_command)
    app.cli.add_command(seed_historico_command)

    return app
