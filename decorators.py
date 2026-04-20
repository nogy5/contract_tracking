# decorators.py
from functools import wraps
from flask import render_template
from sqlalchemy.exc import IntegrityError
import re

def handle_integrity_exceptions(f):
    """Decorador para manejar errores de integridad en funciones específicas"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except IntegrityError as e:
            return handle_integrity_error(e)

    return decorated_function


def handle_integrity_error(error):
    """Maneja errores de integridad de SQLAlchemy"""

    error_message = str(error.orig)
    constraint_type = 'unknown'
    table_name = None
    column_name = None

    # Lógica de detección de errores...

    return render_template('errors/integrity_error.html',
                           error_message=error_message,
                           constraint_type=constraint_type,
                           table_name=table_name,
                           column_name=column_name,
                           error_type='Error de Integridad'), 400