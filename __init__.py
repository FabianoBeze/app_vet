
import os
from flask import Flask
from .extensions import db, login_manager
from .routes.main import main as main_blueprint
from .models import User

def create_app():
    # Obter o diretório base do projeto
    basedir = os.path.abspath(os.path.dirname(__file__))

    app = Flask(__name__, instance_path=os.path.join(basedir, 'instance'))

    # Configuração da aplicação
    app.config['SECRET_KEY'] = 'uma-chave-secreta-bem-dificil'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'pets.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar extensões com a aplicação
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Registrar blueprint
    app.register_blueprint(main_blueprint)

    return app
