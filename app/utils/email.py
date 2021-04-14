from threading import Thread

from flask import render_template
from flask_mail import Mail, Message


class EMail:
    def __init__(self, mail):
        self._mail = mail

    @property
    def mail(self):
        return self._mail

    def init_app(self, app):
        self._app = app
        self._mail.init_app(app)

    def send(self, subject, to, body):
        message = Message(subject, recipients=[to], body=body)
        thr = Thread(target=self._send_async_mail, args=[message])
        thr.start()
        return thr

    def send_html(self, subject, to, html_path, body_path=None, **kwargs):
        message = Message(
            subject, recipients=[to], html=render_template(html_path, **kwargs),
        )
        if body_path:
            message.body = render_template(body_path, **kwargs)
        thr = Thread(target=self._send_async_mail, args=[message])
        thr.start()
        return thr

    def _send_async_mail(self, message):
        with self._app.app_context():
            self._mail.send(message)


email = EMail(Mail())
