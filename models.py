from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    contact = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=True)
    clinic = db.relationship('Clinic', backref=db.backref('users', lazy=True))
    animais = db.relationship('Animal', backref='dono', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    contact = db.Column(db.String(100), nullable=False)

class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    especie = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer, nullable=True)
    contato = db.Column(db.String(100), nullable=True)
    procedimento = db.Column(db.String(200), nullable=True)
    dono_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey("clinic.id"), nullable=True)
    data_agendamento = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Aguardando agendamento')
    verification_token = db.Column(db.String(64), nullable=True)
    token_validated = db.Column(db.Boolean, nullable=False, default=False)
    data_conclusao = db.Column(db.DateTime, nullable=True)
    clinic = db.relationship('Clinic', backref=db.backref('animais', lazy=True))

    @property
    def agendamento(self):
        return self.data_agendamento.strftime('%d/%m/%Y %H:%M') if self.data_agendamento else ''
