from flask import render_template


def page_not_found(e):
    return render_template('errors/404.html'), 404


def internal_server_error(e):
    return render_template('errors/500.html'), 500


def init_app(app):
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_server_error)
