# app/routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
import werkzeug.utils
from app import db
from app.models.user import User
from app.forms.auth import LoginForm, RegistrationForm

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('contracts.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Usuario o contraseña inválidos')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or next_page.startswith('http') or '//' in next_page:
            next_page = url_for('contracts.index')
        return redirect(next_page)
    try:
        return render_template('auth/login.html', title='Iniciar sesión', form=form)
    except Exception as e:
        print(f"Error al renderizar plantilla: {e}")
        # Intenta una plantilla simple directamente en la carpeta templates
        return render_template('error.html')  # crea este archivo en app/templates/


@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('contracts.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('¡Registro exitoso! Ahora puedes iniciar sesión.')
        return redirect(url_for('auth.login'))
    try:
        return render_template('auth/register.html', title='Registro', form=form)
    except Exception as e:
        print(f"Error al renderizar plantilla: {e}")
        # Intenta una plantilla simple directamente en la carpeta templates
        return render_template('error.html')  # crea este archivo en app/templates/