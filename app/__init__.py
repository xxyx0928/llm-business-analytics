from flask import Flask
import os

app = Flask(__name__)

app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(BASE_DIR, 'output')
app.config['DATABASE_FOLDER'] = os.path.join(BASE_DIR, 'database')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATABASE_FOLDER'], exist_ok=True)

from app import routes