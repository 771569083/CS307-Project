from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Boolean
from werkzeug.security import check_password_hash, generate_password_hash

from database.models import (
    Base, engine, session,
    Department, Course, Class, People, Semester,
    ClassPeople,
)

from ..others import login_manager
try:
    from ..config.common import CONFIRMATION_TOKEN_EXPIRATION
except:
    from ..config.common_demo import CONFIRMATION_TOKEN_EXPIRATION


class PeopleExt(UserMixin, Base):
    __tablename__ = 'people_ext'

    id = Column(Integer, primary_key=True)
    uid = Column(Integer, nullable=False, unique=True)
    email = Column(String(64), nullable=False)
    password = Column(String(128), nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=False)

    def __init__(self, uid, email, password, is_admin=False):
        self.uid = uid
        self.email = email
        self.is_admin = is_admin
        self.is_active = False
        self.password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    def generate_confirmation_token(self, expiration=CONFIRMATION_TOKEN_EXPIRATION):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.is_active = True
        session.commit()
        return True


@login_manager.user_loader
def load_user(id):
    return session.query(PeopleExt).filter_by(id=id).first()
