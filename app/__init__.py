from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    db.init_app(app)

    # подключаем страницы
    from .blueprints.pages import bp as pages_bp
    app.register_blueprint(pages_bp)

    return app
