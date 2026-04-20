# app/forms/document.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import TextAreaField, SubmitField
from wtforms.validators import Optional, Length

class DocumentForm(FlaskForm):
    file = FileField('Archivo', validators=[FileRequired()])
    description = TextAreaField('Descripción', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Subir')