
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, jsonify, abort
from ..extensions import db
from ..models import User, Animal, Clinic
from .. import services
from sqlalchemy.orm import joinedload
from datetime import datetime

main = Blueprint('main', __name__)

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            username = request.form["username"]
            password = request.form["password"]
            remember = "remember" in request.form
            user = User.query.filter_by(username=username).first()
            # debug info to diagnose login issues
            try:
                print(f"[DEBUG] login attempt user_found={bool(user)}, username={username}, user_id={getattr(user,'id',None)}, role={getattr(user,'role',None)}")
            except Exception:
                print(f"[DEBUG] login attempt: user lookup performed for username={username}")
            if user and user.check_password(password):
                session["user_id"] = user.id
                session["role"] = user.role
                session.permanent = remember
                flash("Login realizado!", "success")
                return redirect(url_for("main.dashboard"))
            else:
                flash("Credenciais inválidas", "danger")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print("--- Login error:\n", tb)
            flash("Ocorreu um erro durante o login. Verifique o log do servidor.", "danger")
    
    return render_template("login.html")

@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if services.get_user_by_username(username):
            flash("Usuário já existe!", "danger")
            return redirect(url_for("main.register"))
        services.create_user(username=username, password=password)
        flash("Cadastro realizado com sucesso!", "success")
        return redirect(url_for("main.login"))
    return render_template("register.html")
@main.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("main.login"))

@main.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("main.login"))
    
    user = db.session.get(User, session["user_id"])
    if not user:
        session.pop('user_id', None)
        session.pop("role", None)
        return redirect(url_for('main.login'))

    # === VISÃO DO ADMIN ===
    if user.role == 'admin':
        all_animals = Animal.query.options(joinedload(Animal.dono), joinedload(Animal.clinic)).order_by(Animal.id.desc()).all()
        
        # Dados para os gráficos (sem alterações)
        procedimentos = [animal.procedimento.lower() for animal in all_animals if animal.procedimento]
        procedimento_counts = {
            'castração': procedimentos.count('castração'),
            'consulta': procedimentos.count('consulta'),
            'vacinação': procedimentos.count('vacinação'),
            'outros': len([p for p in procedimentos if p not in ['castração', 'consulta', 'vacinação']])
        }
        status_counts = {
            'Concluído': len([a for a in all_animals if a.status == 'Concluído']),
            'Aguardando': len([a for a in all_animals if a.status != 'Concluído'])
        }

        return render_template("admin_dashboard.html", user=user, animals=all_animals, procedimento_counts=procedimento_counts, status_counts=status_counts)

    # === VISÃO DA CLÍNICA ===
    elif user.role == 'clinic':
        return redirect(url_for('main.clinic_dashboard'))

    # === VISÃO DO TUTOR ===
    elif user.role == 'user':
        user_animals = Animal.query.filter_by(dono_id=user.id).order_by(Animal.id.desc()).all()
        return render_template("user_dashboard.html", user=user, animals=user_animals)
    
    return "Tipo de usuário desconhecido."

@main.route("/clinic_dashboard")
def clinic_dashboard():
    if "user_id" not in session or session.get("role") != "clinic":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("main.login"))

    user = db.session.get(User, session["user_id"])
    if not user or not user.clinic_id:
        flash("Usuário da clínica não associado a uma clínica.", "danger")
        return redirect(url_for("main.login"))

    # Animais já atribuídos a esta clínica
    clinic_animals = Animal.query.filter_by(clinic_id=user.clinic_id).order_by(Animal.id.desc()).all()
    
    # Animais disponíveis para serem reivindicados
    available_animals = Animal.query.filter_by(clinic_id=None).order_by(Animal.id.desc()).all()

    return render_template("clinic_dashboard.html", user=user, clinic_name=user.clinic.name, clinic_animals=clinic_animals, available_animals=available_animals)

@main.route("/claim_animal/<int:animal_id>", methods=["POST"])
def claim_animal(animal_id):
    if "user_id" not in session or session.get("role") != "clinic":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("main.login"))

    user = db.session.get(User, session["user_id"])
    animal = Animal.query.get_or_404(animal_id)

    if animal.clinic_id:
        flash("Este animal já foi reivindicado por outra clínica.", "warning")
    else:
        animal.clinic_id = user.clinic_id
        animal.status = "Aguardando agendamento"
        db.session.commit()
        flash(f"Você reivindicou o atendimento para {animal.nome}.", "success")
    
    return redirect(url_for("main.clinic_dashboard"))
    
@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))

@main.route("/schedule/<int:animal_id>", methods=["GET", "POST"])
def schedule(animal_id):
    if "user_id" not in session or session.get("role") != "clinic":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("main.login"))

    animal = Animal.query.get_or_404(animal_id)
    user = db.session.get(User, session["user_id"])

    if animal.clinic_id != user.clinic_id:
        flash("Este animal não pertence à sua clínica.", "danger")
        return redirect(url_for("main.clinic_dashboard"))

    if request.method == "POST":
        data_str = request.form.get("data_agendamento")
        if data_str:
            try:
                animal.data_agendamento = datetime.strptime(data_str, '%Y-%m-%dT%H:%M')
                animal.status = "Agendado"
                animal.verification_token = services.generate_token()
                db.session.commit()
                flash(f"Atendimento para {animal.nome} agendado! Token: {animal.verification_token}", "success")
                return redirect(url_for("main.clinic_dashboard"))
            except ValueError:
                flash("Formato de data inválido. Use o formato YYYY-MM-DDTHH:MM.", "danger")
        else:
            flash("A data de agendamento é obrigatória.", "danger")
        
        return redirect(url_for('main.schedule', animal_id=animal.id))

    return render_template("schedule.html", animal=animal)

@main.route("/mark_as_complete/<int:animal_id>", methods=["POST"])
def mark_as_complete(animal_id):
    if "user_id" not in session or session.get("role") != "clinic":
        abort(403)

    animal = Animal.query.get_or_404(animal_id)
    user = db.session.get(User, session["user_id"])

    if animal.clinic_id != user.clinic_id:
        flash("Este animal não pertence à sua clínica.", "danger")
        return redirect(url_for("main.dashboard"))

    animal.status = "Concluído"
    animal.token_validated = True
    db.session.commit()
    flash(f"Atendimento para {animal.nome} marcado como concluído.", "success")

    return redirect(url_for("main.dashboard"))
    
@main.route('/assign_clinic', methods=['POST'])
def assign_clinic():
    if 'user_id' not in session or db.session.get(User, session['user_id']).role != 'admin':
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for('main.login'))
    animal_id = request.form.get('animal_id')
    clinic_id = request.form.get('clinic_id')
    
    if not animal_id or not clinic_id:
        flash("Animal ou clínica inválida.", "danger")
        return redirect(url_for('main.dashboard'))

    animal = services.assign_clinic_to_animal(animal_id, clinic_id)
    if not animal:
        flash("Erro ao atribuir clínica.", "danger")
    else:
        flash(f"Clínica atribuída com sucesso para o animal {animal.nome}!", "success")

    return redirect(url_for('main.dashboard'))
    
@main.route('/_debug/users')
def _debug_users():
    # disponível apenas em modo debug local
    if not current_app.debug:
        abort(404)
    users = User.query.with_entities(User.id, User.username, User.role, User.email).all()
    return jsonify([{'id': u[0], 'username': u[1], 'role': u[2], 'email': u[3]} for u in users])


@main.route('/_debug/animals')
def _debug_animals():
    if not current_app.debug:
        abort(404)
    animals = Animal.query.with_entities(Animal.id, Animal.nome, Animal.status, Animal.verification_token, Animal.token_validated, Animal.data_agendamento).all()
    out = []
    for a in animals:
        out.append({'id': a[0], 'nome': a[1], 'status': a[2], 'token': a[3], 'token_validated': bool(a[4]), 'agendamento': str(a[5]) if a[5] else None})
    return jsonify(out)


@main.route('/_debug/current_user')
def _debug_current_user():
    if not current_app.debug:
        abort(404)
    data = {'session': dict(session)}
    uid = session.get('user_id')
    if uid:
        u = User.query.get(uid)
        data['user'] = {'id': u.id, 'username': u.username, 'role': u.role, 'clinic_id': u.clinic_id}
    return jsonify(data)


@main.route('/validate_token/<int:animal_id>', methods=['POST'])
def validate_token(animal_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = db.session.get(User, session.get('user_id'))
    if not user or user.role not in ['clinic', 'admin']:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    token = request.form.get('token')
    if not token:
        flash('Token obrigatório.', 'danger')
        return redirect(url_for('main.dashboard'))

    ok = services.validate_token(animal_id, token)
    if ok:
        flash('Token validado com sucesso.', 'success')
    else:
        flash('Token inválido.', 'danger')
    return redirect(url_for('main.dashboard'))




@main.route('/admin/add_clinic', methods=['GET', 'POST'])
def add_clinic():
    if "user_id" not in session or session.get("role") != "admin":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("main.login"))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        contact = request.form['contact']
        
        existing_clinic = Clinic.query.filter_by(name=username).first()
        if existing_clinic:
            flash('Clínica com esse nome já existe.', 'danger')
            return redirect(url_for('main.add_clinic'))
        # create the Clinic record
        clinic = services.create_clinic(name=username, contact=contact)
        # create the user account linked to clinic
        services.create_user(username=username, password=password, role='clinic', email=email, contact=contact, clinic_id=clinic.id)
        flash('Clínica adicionada com sucesso!', 'success')
        return redirect(url_for('main.manage_clinics'))

    return render_template("add_clinic.html")
    
@main.route("/edit_clinic/<int:clinic_id>", methods=["GET", "POST"])
def edit_clinic(clinic_id):
    if "user_id" not in session or session["role"] != "admin":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("main.login"))
    
    clinic = Clinic.query.get_or_404(clinic_id)

    if request.method == "POST":
        clinic.name = request.form["name"]
        clinic.contact = request.form["contact"]
        db.session.commit()
        flash("Clínica atualizada com sucesso!", "success")
        return redirect(url_for("main.manage_clinics"))

    return render_template("edit_clinic.html", clinic=clinic)

@main.route("/delete_clinic/<int:clinic_id>", methods=["POST"])
def delete_clinic(clinic_id):
    if "user_id" not in session:
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("main.login"))
    if session.get("role") != "admin":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("main.dashboard"))
    
    clinic = Clinic.query.get_or_404(clinic_id)
    db.session.delete(clinic)
    db.session.commit()
    flash("Clínica excluída com sucesso!", "success")
    return redirect(url_for("main.manage_clinics"))


@main.route("/update_animal_status/<int:animal_id>", methods=["POST"])
def update_animal_status(animal_id):
    if "user_id" not in session or session["role"] != 'clinic':
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("main.login"))

    animal = Animal.query.get_or_404(animal_id)
    user = User.query.get(session["user_id"])

    # Garante que o animal pertence à clínica que está tentando atualizá-lo
    if animal.clinic_id != user.clinic_id:
        flash("Você não tem permissão para atualizar este animal.", "danger")
        return redirect(url_for("main.dashboard"))

    new_status = request.form.get("status")
    if new_status == 'Concluído':
        services.mark_animal_complete(animal_id)
        flash(f"Status do animal {animal.nome} atualizado para {new_status}.", "success")
    else:
        flash("Status inválido.", "danger")

    return redirect(url_for("main.dashboard"))

@main.route("/reports")
def reports():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    user = User.query.get(session["user_id"])
    print(f"[DEBUG reports] session_user_id={session.get('user_id')} session_role={session.get('role')}")
    try:
        print(f"[DEBUG reports] user.id={user.id} user.role={user.role} user.clinic_id={user.clinic_id}")
    except Exception:
        print('[DEBUG reports] could not read user attributes')
    clinics_data = []
    clinic_data = None

    if user.role == 'admin':
        # Admin view: Group completed animals by clinic
        completed_animals = Animal.query.filter_by(status='Concluído').options(joinedload(Animal.clinic), joinedload(Animal.dono)).all()
        clinics_map = {}
        for animal in completed_animals:
            if animal.clinic:
                if animal.clinic.id not in clinics_map:
                    clinics_map[animal.clinic.id] = {'name': animal.clinic.name, 'animals': []}
                clinics_map[animal.clinic.id]['animals'].append(animal)
        clinics_data = list(clinics_map.values())
        print(f"[DEBUG reports] admin found {len(clinics_data)} clinics with completed animals")

    elif user.role == 'clinic' and user.clinic_id:
        # Clinic view: Show only their completed animals
        completed_animals = Animal.query.filter_by(status='Concluído', clinic_id=user.clinic_id).options(joinedload(Animal.dono)).all()
        print(f"[DEBUG reports] clinic completed_animals count = {len(completed_animals)} for clinic_id={user.clinic_id}")
        clinic_name = Clinic.query.get(user.clinic_id).name
        clinic_data = {'name': clinic_name, 'animals': completed_animals}

    return render_template("reports.html", user=user, clinics_data=clinics_data, clinic_data=clinic_data)


# ----------------- ROTAS DE CLÍNICA (ADMIN) -----------------

def manage_clinics():
    if "user_id" not in session:
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("main.login"))
    if session.get("role") != "admin":
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for("main.dashboard"))
    
    clinics = Clinic.query.all()
    return render_template("manage_clinics.html", clinics=clinics)


