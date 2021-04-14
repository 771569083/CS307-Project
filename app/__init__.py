__import__('sys').path.append('..')


from flask import Flask

from . import errors
from . import others
from .utils.email import email

from .views.user import user_blueprint


app = Flask(__name__)
try:
    app.config.from_pyfile('config/common.py')
except FileNotFoundError:
    app.config.from_pyfile('config/common_demo.py')

email.init_app(app)
errors.init_app(app)
others.init_app(app)

app.register_blueprint(user_blueprint)


@app.route('/')
def index():
    return 'hello world'
