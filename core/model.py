"""
Base Model - Lớp cơ sở cho tất cả models
Cung cấp CRUD operations chung
"""
from core.database import db


class BaseModel:
    """Lớp model cơ sở với các phương thức CRUD"""

    # Tên bảng - override trong subclass
    table_name = ''

    @classmethod
    def get_all(cls, where="1=1", params=None, order_by="id DESC", limit=None, offset=None):
        """
        Lấy tất cả bản ghi theo điều kiện
        Hỗ trợ phân trang (limit/offset)
        """
        sql = f"SELECT * FROM {cls.table_name} WHERE {where} ORDER BY {order_by}"
        if limit:
            sql += f" LIMIT {limit}"
            if offset:
                sql += f" OFFSET {offset}"
        return db.query(sql, params)

    @classmethod
    def get_by_id(cls, record_id):
        """Lấy bản ghi theo ID"""
        sql = f"SELECT * FROM {cls.table_name} WHERE id = %s"
        return db.get_one(sql, (record_id,))

    @classmethod
    def create(cls, data: dict):
        """
        Tạo bản ghi mới
        data: dict {tên_cột: giá_trị}
        Trả về ID bản ghi mới
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        sql = f"INSERT INTO {cls.table_name} ({columns}) VALUES ({placeholders})"
        return db.execute(sql, tuple(data.values()))

    @classmethod
    def update(cls, record_id, data: dict):
        """
        Cập nhật bản ghi theo ID
        data: dict {tên_cột: giá_trị_mới}
        """
        set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        sql = f"UPDATE {cls.table_name} SET {set_clause} WHERE id = %s"
        values = list(data.values()) + [record_id]
        return db.execute(sql, tuple(values))

    @classmethod
    def delete(cls, record_id):
        """Xóa bản ghi theo ID"""
        sql = f"DELETE FROM {cls.table_name} WHERE id = %s"
        return db.execute(sql, (record_id,))

    @classmethod
    def count(cls, where="1=1", params=None):
        """Đếm số bản ghi"""
        return db.count(cls.table_name, where, params)

    @classmethod
    def find_by(cls, column, value):
        """Tìm bản ghi theo cột cụ thể"""
        sql = f"SELECT * FROM {cls.table_name} WHERE {column} = %s"
        return db.get_one(sql, (value,))

    @classmethod
    def find_all_by(cls, column, value, order_by="id DESC"):
        """Tìm tất cả bản ghi theo cột cụ thể"""
        sql = f"SELECT * FROM {cls.table_name} WHERE {column} = %s ORDER BY {order_by}"
        return db.query(sql, (value,))

    @classmethod
    def paginate(cls, page=1, per_page=10, where="1=1", params=None, order_by="id DESC"):
        """
        Phân trang kết quả
        Trả về: {items, total, page, per_page, total_pages}
        """
        total = cls.count(where, params)
        total_pages = (total + per_page - 1) // per_page
        offset = (page - 1) * per_page

        items = cls.get_all(
            where=where,
            params=params,
            order_by=order_by,
            limit=per_page,
            offset=offset
        )

        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages
        }

    @classmethod
    def search(cls, columns, keyword, order_by="id DESC", limit=20):
        """
        Tìm kiếm theo nhiều cột
        columns: list tên cột cần tìm
        keyword: từ khóa
        """
        conditions = ' OR '.join([f"{col} LIKE %s" for col in columns])
        sql = f"SELECT * FROM {cls.table_name} WHERE {conditions} ORDER BY {order_by} LIMIT {limit}"
        params = tuple([f"%{keyword}%"] * len(columns))
        return db.query(sql, params)
