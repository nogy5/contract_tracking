# app/forms/contract.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, DecimalField, SelectField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class ContractForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descripción', validators=[Optional(), Length(max=500)])
    contract_number = StringField('Número de Contrato', validators=[DataRequired(), Length(max=50)])
    start_date = DateField('Fecha de Inicio', validators=[DataRequired()])
    end_date = DateField('Fecha de Finalización', validators=[Optional()])
    indefinite_contract = BooleanField('Contrato indefinido')  # Nuevo campo checkbox
    value = DecimalField('Valor del Contrato', validators=[Optional(), NumberRange(min=0)])
    # --- NUEVOS CAMPOS AÑADIDOS ---
    payment_period = StringField('Periodo de Pago', validators=[Optional(), Length(max=100)])
    payment_entry = StringField('Ingreso a pago', validators=[Optional(), Length(max=100)])
    # ------------------------------
    facturacion = DecimalField('Facturación', validators=[Optional(), NumberRange(min=0)])
    counterparty = StringField('Cliente', validators=[DataRequired(), Length(max=100)])
    status = SelectField('Estado', choices=[
        ('activo', 'Activo'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
        ('en_revision', 'En Revisión'),
        ('vencido', 'Vencido'),
        ('suspendido', 'Suspendido')
    ], validators=[DataRequired()])
    submit = SubmitField('Guardar')

    def validate(self, extra_validators=None):
        """Validación personalizada"""
        if not super().validate(extra_validators):
            return False

        # Si no es indefinido, la fecha de finalización es requerida
        if not self.indefinite_contract.data and not self.end_date.data:
            self.end_date.errors.append('La fecha de finalización es requerida para contratos con duración definida.')
            return False

        # Si es indefinido, limpiar la fecha de finalización
        if self.indefinite_contract.data:
            self.end_date.data = None

        # Validar que la fecha de fin sea posterior a la de inicio
        if self.end_date.data and self.start_date.data:
            if self.end_date.data <= self.start_date.data:
                self.end_date.errors.append('La fecha de finalización debe ser posterior a la fecha de inicio.')
                return False

        return True

class MilestoneForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descripción', validators=[Optional(), Length(max=500)])
    due_date = DateField('Fecha de Vencimiento', validators=[DataRequired()])
    submit = SubmitField('Guardar')