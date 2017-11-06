from flask import render_template, redirect, request, url_for, flash, request
from flask_login import login_user, login_required, logout_user
from . import auth
from ..models import User
from .forms import LoginForm, RegistrationForm
from .. import db
from ..email import send_email
from flask_login import current_user


@auth.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password')

    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('you have been logged out.')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        print(user.role)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm your account','auth/email/confirm', user=user, token=token)
        flash('A confirmation email has been sent to you by email.')

        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


@auth.before_app_request
def before_request():

    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
            and request.endpoint[:5]!='auth.':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))