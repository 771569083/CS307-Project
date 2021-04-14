from flask_bootstrap import Bootstrap
from flask_cors import CORS
from flask_login import LoginManager


bootstrap = Bootstrap()
cors = CORS()
login_manager = LoginManager()


def init_app(app):
    bootstrap.init_app(app)
    cors.init_app(app)
    login_manager.init_app(app)
