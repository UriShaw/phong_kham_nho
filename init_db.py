"""
Script khoi tao database
Chay: python init_db.py
"""
import sys
import re

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash
from config import Config


def init_database():
    """Khoi tao database tu schema.sql"""
    print("[...] Dang khoi tao database...")

    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASS,
            charset='utf8mb4'
        )
        cursor = conn.cursor()

        # Tao database
        cursor.execute("CREATE DATABASE IF NOT EXISTS medpro_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute("USE medpro_db")
        conn.commit()
        print("[OK] Tao database medpro_db thanh cong!")

        # Doc file SQL
        # Tự động tìm file SQL trong thư mục database
        import os
        sql_file = 'database/medpro_db.sql'
        if not os.path.exists(sql_file):
            sql_file = 'database/schema.sql'
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Xoa comment dong --
        lines = []
        for line in sql_content.split('\n'):
            stripped = line.strip()
            # Bo qua comment thuan tuy
            if stripped.startswith('--'):
                continue
            # Bo qua CREATE DATABASE va USE
            upper = stripped.upper()
            if upper.startswith('CREATE DATABASE') or upper.startswith('USE '):
                continue
            lines.append(line)

        sql_clean = '\n'.join(lines)

        # Tach cau lenh bang dau ;
        statements = sql_clean.split(';')
        count = 0
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue
            try:
                cursor.execute(stmt)
                conn.commit()
                count += 1
            except Error as e:
                msg = str(e).lower()
                if 'already exists' in msg or 'duplicate' in msg:
                    pass
                else:
                    print(f"  [WARN] {e}")

        print(f"[OK] Da thuc thi {count} cau lenh SQL!")

        # Password hash da duoc nhung truc tiep trong schema.sql
        print("[OK] Mat khau da co san trong SQL (khong can cap nhat).")

        cursor.close()
        conn.close()

        print("")
        print("[DONE] Khoi tao database hoan tat!")
        print("")
        print("[INFO] Tai khoan mau:")
        print("------------------------------------------")
        print("  Admin:     admin@medpro.vn / admin123")
        print("  Bac si:    bs.nguyen@medpro.vn / bacsi123")
        print("  Benh nhan: bn.nguyen@medpro.vn / benhnhan123")
        print("------------------------------------------")
        print("")
        print("[RUN] Chay server: .venv\\Scripts\\python.exe run.py")
        print("[URL] Truy cap:    http://localhost:5000")

    except Error as e:
        print(f"\n[ERROR] Loi ket noi MySQL: {e}")
        print("\n[TIP] Kiem tra:")
        print("  1. XAMPP da khoi dong MySQL chua?")
        print("  2. Port 3306 co bi chiem khong?")
        print("  3. User/password MySQL dung chua?")


if __name__ == '__main__':
    init_database()
