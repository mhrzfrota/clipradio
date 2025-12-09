import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    
    # CORS
    CORS_ORIGINS = "*"
    
    # Storage
    STORAGE_PATH = os.path.join(os.path.dirname(__file__), 'storage')
    UPLOAD_PATH = os.path.join(os.path.dirname(__file__), 'uploads')
    
    @staticmethod
    def init_app(app):
        os.makedirs(Config.STORAGE_PATH, exist_ok=True)
        os.makedirs(Config.UPLOAD_PATH, exist_ok=True)
        os.makedirs(os.path.join(Config.STORAGE_PATH, 'audio'), exist_ok=True)
        os.makedirs(os.path.join(Config.STORAGE_PATH, 'clips'), exist_ok=True)

