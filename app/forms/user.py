from flask_wtf import FlaskForm
from wtforms import (
    IntegerField, StringField, PasswordField, BooleanField, SubmitField,
    ValidationError,
)
from wtforms.validators import Required, Length, Email, Regexp, EqualTo

from ..database.utils import get


class LoginForm(FlaskForm):
    uid = IntegerField('学工号', validators=[Required()])
    password = PasswordField('密码', validators=[Required()]) 
    remember_me = BooleanField('记住密码')
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):
    uid = IntegerField('学工号', validators=[Required()])
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    password = PasswordField('密码', validators=[Required()])
    password2 = PasswordField('确认密码', validators=[Required(), EqualTo('password', message='两次密码必须一致。')])
    submit = SubmitField('注册')

    def validate_uid(self, field):
        if get.user(field.data):
            raise ValidationError('当前学工号已经注册过。')

    def validate_email(self, field):
        if not field.data.endswith('@mail.sustech.edu.cn'):
            raise ValidationError('当前仅支持通过南方科技大学邮箱注册。')
