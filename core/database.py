"""
Database - Kết nối và quản lý MySQL
Sử dụng connection pooling để tối ưu hiệu năng
"""
import mysql.connector
from mysql.connector import pooling, Error
from config import Config


class Database:
    """Singleton class quản lý kết nối MySQL"""

    _instance = None
    _pool = None

    def __new__(cls):
        """Đảm bảo chỉ có 1 instance (Singleton pattern)"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Khởi tạo connection pool"""
        if self._pool is None:
            try:
                self._pool = pooling.MySQLConnectionPool(
                    pool_name="medpro_pool",
                    pool_size=5,
                    pool_reset_session=True,
                    host=Config.DB_HOST,
                    port=Config.DB_PORT,
                    user=Config.DB_USER,
                    password=Config.DB_PASS,
                    database=Config.DB_NAME,
                    charset='utf8mb4',
                    collation='utf8mb4_unicode_ci',
                    autocommit=True
                )
                print("[OK] Ket noi MySQL thanh cong!")
            except Error as e:
                print(f"[ERROR] Loi ket noi MySQL: {e}")
                self._pool = None

    def get_connection(self):
        """Lấy connection từ pool"""
        try:
            if self._pool:
                return self._pool.get_connection()
            return None
        except Error as e:
            print(f"[ERROR] Loi lay connection: {e}")
            return None

    def query(self, sql, params=None):
        """
        Thực thi câu truy vấn SELECT
        Trả về danh sách dict
        """
        conn = self.get_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(sql, params or ())
            result = cursor.fetchall()
            cursor.close()
            return result
        except Error as e:
            print(f"[ERROR] Loi truy van: {e}")
            return []
        finally:
            conn.close()

    def get_one(self, sql, params=None):
        """
        Thực thi truy vấn và trả về 1 bản ghi
        """
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(sql, params or ())
            result = cursor.fetchone()
            cursor.close()
            return result
        except Error as e:
            print(f"[ERROR] Loi truy van: {e}")
            return None
        finally:
            conn.close()

    def execute(self, sql, params=None):
        """
        Thực thi câu lệnh INSERT/UPDATE/DELETE
        Trả về lastrowid hoặc rowcount
        """
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(buffered=True)
            cursor.execute(sql, params or ())
            conn.commit()
            last_id = cursor.lastrowid
            affected = cursor.rowcount
            cursor.close()
            return last_id if last_id else affected
        except Error as e:
            print(f"[ERROR] Loi thuc thi: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def execute_many(self, sql, data_list):
        """
        Thực thi nhiều câu lệnh cùng lúc
        """
        conn = self.get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor(buffered=True)
            cursor.executemany(sql, data_list)
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected
        except Error as e:
            print(f"[ERROR] Loi thuc thi hang loat: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def count(self, table, where="1=1", params=None):
        """Đếm số bản ghi trong bảng"""
        sql = f"SELECT COUNT(*) as total FROM {table} WHERE {where}"
        result = self.get_one(sql, params)
        return result['total'] if result else 0


# Singleton instance
db = Database()
