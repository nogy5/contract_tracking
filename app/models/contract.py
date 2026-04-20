# app/models/contract.py
from datetime import datetime, date
from app import db


class Contract(db.Model):
    __tablename__ = 'contracts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    contract_number = db.Column(db.String(50), unique=True, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    indefinite_contract = db.Column(db.Boolean, default=False)  # Nuevo campo
    value = db.Column(db.Numeric(15, 2))
    # --- NUEVOS CAMPOS AÑADIDOS ---
    payment_period = db.Column(db.String(100))  # Periodo de Pago
    payment_entry = db.Column(db.String(100))  # Ingreso a pago
    # ------------------------------
    facturacion = db.Column(db.Numeric(15, 2))
    facturado   = db.Column(db.Numeric(15, 2), nullable=True, default=0)
    status = db.Column(db.String(20), default='activo')  # activo, finalizado, cancelado, etc.
    counterparty = db.Column(db.String(100), nullable=False)  # Parte contratante
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Claves foráneas
    responsible_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Relaciones
    documents = db.relationship('Document', backref='contract', lazy='dynamic')
    milestones = db.relationship('Milestone', backref='contract', lazy='dynamic')

    def __repr__(self):
        return f'<Contract {self.contract_number}: {self.title}>'

    @property
    def is_active(self):
        return self.status == 'activo'

    @property
    def is_expired(self):
        if self.indefinite_contract or not self.end_date:
            return False
        return self.end_date < datetime.now().date()

    @property
    def days_until_expiry(self):
        if self.indefinite_contract or not self.end_date:
            return None
        delta = self.end_date - datetime.now().date()
        return delta.days

    @property
    def days_remaining(self):
        if self.indefinite_contract or not self.end_date:
            return None
        today = date.today()
        delta = self.end_date - today
        return delta.days

    @property
    def days_remaining_text(self):
        if self.indefinite_contract:
            return "Contrato indefinido"

        if not self.end_date:
            return "Sin fecha de finalización"

        days = self.days_remaining
        if days < 0:
            return f"Vencido hace {abs(days)} días"
        elif days == 0:
            return "Vence hoy"
        elif days == 1:
            return "Vence mañana"
        else:
            return f"Vence en {days} días"

class Milestone(db.Model):
    __tablename__ = 'milestones'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Clave foránea
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)

    def __repr__(self):
        return f'<Milestone {self.title}>'