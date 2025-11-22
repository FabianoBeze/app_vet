from .extensions import db
from .models import User, Animal, Clinic
import random

def generate_token():
    """Gera um token numérico de 6 dígitos para verificação."""
    return f"{random.randint(0, 999999):06d}"

# Funções de serviço para isolar lógica de acesso ao DB

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()


def create_user(username, password, role='user', email=None, contact=None, clinic_id=None):
    user = User(username=username, email=email, contact=contact, role=role, clinic_id=clinic_id)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def get_clinics():
    return Clinic.query.all()

def get_clinic_by_id(clinic_id):
    return Clinic.query.get(clinic_id)

def create_clinic(name, contact):
    clinic = Clinic(name=name, contact=contact)
    db.session.add(clinic)
    db.session.commit()
    return clinic

def create_animal(nome, especie, contato, procedimento, dono_id, status='Aguardando'):
    animal = Animal(nome=nome, especie=especie, contato=contato, procedimento=procedimento, dono_id=dono_id, status=status)
    db.session.add(animal)
    db.session.commit()
    return animal

def assign_clinic_to_animal(animal_id, clinic_id):
    animal = Animal.query.get(animal_id)
    if not animal:
        return None
    animal.clinic_id = clinic_id
    db.session.commit()
    return animal

def claim_animal_for_clinic(animal_id, clinic_id):
    """Try to claim (assign) an animal to a clinic in a safe way.

    Returns the animal if the claim succeeded, or None if the animal was
    already claimed or not in 'Aguardando' status.
    """
    # SQLite doesn't support SELECT ... FOR UPDATE; we'll perform a short
    # transaction: reload the object, check status, assign and commit.
    try:
        animal = Animal.query.get(animal_id)
        if not animal:
            return None
        # Only allow claiming when status starts with 'Aguard' (covers 'Aguardando' and variants)
        if not (str(animal.status).startswith('Aguard')) or animal.clinic_id:
            return None
        animal.clinic_id = clinic_id
        db.session.commit()
        return animal
    except Exception:
        db.session.rollback()
        return None

def schedule_animal(animal_id, dt):
    animal = Animal.query.get(animal_id)
    if not animal:
        return None
    animal.data_agendamento = dt
    animal.status = 'Agendado'
    # gerar token numérico de 6 dígitos para verificação pelo tutor
    token = generate_token()
    animal.verification_token = token
    animal.token_validated = False
    db.session.commit()

    # send token via SMS (simulated) to the tutor's contact if available
    tutor = None
    try:
        tutor = User.query.get(animal.dono_id)
    except Exception:
        tutor = None

    if tutor and getattr(tutor, 'contact', None):
        try:
            send_sms(tutor.contact, f"Seu agendamento para {animal.nome} foi confirmado. Token: {token}")
        except Exception:
            # ignore SMS failures in this simulated environment
            pass

    return animal


def send_sms(phone_number, message):
    """Simula o envio de um SMS escrevendo em instance/sms.log.

    Em produção, substitua esta função por integração com um provedor (Twilio,
    MessageBird, etc.).
    """
    import os
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_dir = os.path.join(basedir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    sms_log = os.path.join(instance_dir, 'sms.log')
    from datetime import datetime
    line = f"{datetime.utcnow().isoformat()} SMS to {phone_number}: {message}\n"
    with open(sms_log, 'a', encoding='utf-8') as f:
        f.write(line)
    # also print to stdout for debug
    print('[SMS]', line.strip())
    return True


def validate_token(animal_id, token):
    animal = Animal.query.get(animal_id)
    if not animal:
        return False
    if animal.verification_token and str(animal.verification_token) == str(token):
        animal.token_validated = True
        db.session.commit()
        return True
    return False


def mark_animal_complete(animal_id):
    animal = Animal.query.get(animal_id)
    if not animal:
        return None
    from datetime import datetime
    animal.status = 'Concluído'
    animal.data_conclusao = datetime.utcnow()
    db.session.commit()
    return animal
