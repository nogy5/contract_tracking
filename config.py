# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Pr0t1c26'
    # Cambia 'tu_contraseña_real' por la clave que usas en pgAdmin
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://protic:Pr0t1c26@localhost:5432/contract_tracking'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app/static/uploads')
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # Limitar uploads a 16MB

