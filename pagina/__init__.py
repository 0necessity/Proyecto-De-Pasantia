from flask import Flask, request
import os

def create_app():
    app = Flask(__name__, static_url_path='/static')
    app.config["SECRET_KEY"] = "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"
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'maybe')

    from .views import views
    from .auth import auth

    @app.errorhandler(404)
    def page_not_found(error):
        print(request.path)
        return "NOt found 404"

    @app.errorhandler(500)
    def page_not_found(error):
        print(request.path)
        return "NOt found 500"

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")

    return app

