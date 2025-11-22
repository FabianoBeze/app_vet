from . import create_app, db
from models import User

app = create_app()

def init_db():
    """Inicializa o banco de dados e cria o usuário admin se necessário."""
    with app.app_context():
        db.create_all()

        # Adicionar dados iniciais (admin) se não existirem
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', role='admin')
            admin_user.set_password('admin')
            db.session.add(admin_user)
            db.session.commit()

if __name__ == "__main__":
    init_db()
    # use_reloader=False evita reinicializações inesperadas causadas pelo watchdog
    # monitorando os arquivos errados.
    app.run(debug=True, host='0.0.0.0', use_reloader=False)