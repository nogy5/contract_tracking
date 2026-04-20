# run.py
from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # ¡IMPORTANTE! Debes importar los modelos para que SQLAlchemy los reconozca
        from app.models.contract import Contract, Milestone
        from app.models.user import User
        # Importa aquí cualquier otro modelo (Notification, Document, etc.)

        # Ahora sí, creará las tablas de los modelos importados
        db.create_all()
        print("Tablas creadas exitosamente.")

    app.run(debug=True)