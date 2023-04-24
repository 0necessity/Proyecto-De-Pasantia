from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path

db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__, static_url_path='/static')
    app.config["SECRET_KEY"] = "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"
    app.config['UPLOAD_FOLDER'] = r"C:\Users\pbedg\Desktop\Nueva carpeta (7)\yes\pagina\maybe"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_NAME}"
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")

    from .models import User
    create_database(app)
    return app


def create_database(app):
    if not path.exists("pagina/" + DB_NAME):
        with app.app_context():
            db.create_all()