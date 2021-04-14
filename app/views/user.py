import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request,
    session, url_for,
)
from flask_login import login_user, logout_user, login_required

from ..database.models import PeopleExt
from ..database.utils import add, get
from ..forms.user import LoginForm, RegistrationForm
from ..utils.email import email


user_blueprint = Blueprint('user', __name__, url_prefix='/user')


@user_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = get.user(form.uid.data)
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('index'))
        flash('账户或者密码不正确。')
    return render_template('user/login.html', form=form)


@user_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash('你已经退出登录！')
    return redirect(url_for('index'))


@user_blueprint.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = add.user(form.uid.data, form.email.data, form.password.data)
        token = user.generate_confirmation_token()
        email.send_html(
            '[DataHub] 确认您的账户', form.email.data, 'emails/register.html', 'emails/register.txt',
            uid=form.uid.data, url=url_for('user.confirm', token=token.decode(), _external=True),
        )
        flash('账号验证码已发送至邮箱！')
        return redirect(url_for('index'))
    return render_template('user/register.html', form=form)


@user_blueprint.route('/confirm', methods=['GET','POST'])
@login_required
def confirm(token):
    return token
