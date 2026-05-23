"""
Cấu hình hệ thống MedPro
Đọc biến môi trường từ file .env
"""
import os
from dotenv import load_dotenv

# Tải biến môi trường
load_dotenv()


class Config:
    """Cấu hình chính của ứng dụng"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'medpro_default_secret_key')
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'

    # Database MySQL
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASS = os.getenv('DB_PASS', '')
    DB_NAME = os.getenv('DB_NAME', 'medpro_db')

    # Upload file
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

    # Thanh toán MB Bank
    MBBANK_STK = os.getenv('MBBANK_STK', '0965117393')
    MBBANK_TEN = os.getenv('MBBANK_TEN', 'NGUYEN QUOC ANH')
    MBBANK_BANK_ID = os.getenv('MBBANK_BANK_ID', 'MB')

    # SMTP Email
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASS = os.getenv('SMTP_PASS', '')

    # Phiên đăng nhập
    SESSION_LIFETIME = 3600  # 1 giờ (giây)
    PERMANENT_SESSION_LIFETIME = 86400  # 24 giờ
