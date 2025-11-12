from flask import Flask
from settings import Config
from routes.index import index_bp


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    config = Config()

    config.config_init(app)

    app.register_blueprint(index_bp)

    return app
