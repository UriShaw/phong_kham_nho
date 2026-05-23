"""
Seed dữ liệu mẫu cho module Tiện ích sức khỏe.

Chạy: python seed_health_data.py

Tạo dữ liệu mẫu cho:
  - suc_khoe_log: 30 ngày log sức khỏe
  - nhat_ky_tam_trang: 14 ngày nhật ký tâm trạng
  - ai_chan_doan_log: 5 lần chẩn đoán mẫu

Dữ liệu được tạo cho 10 bệnh nhân đầu tiên (benh_nhan_id = 1..10).
"""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import json
import random
from datetime import date, timedelta

import mysql.connector
from config import Config


def get_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASS,
        database='medpro_db',
        charset='utf8mb4',
    )


# ─── Hàm tạo dữ liệu mẫu ────────────────────────────────────────────

def gen_health_logs(benh_nhan_id: int, days: int = 30) -> list[tuple]:
    """Tạo log sức khỏe hàng ngày trong N ngày gần đây."""
    rows = []
    today = date.today()
    base_hr = random.randint(65, 85)
    base_sys = random.randint(110, 130)
    base_dia = random.randint(65, 85)
    base_sleep = round(random.uniform(6.0, 8.0), 1)
    base_weight = round(random.uniform(50.0, 85.0), 1)

    for i in range(days):
        d = today - timedelta(days=days - 1 - i)
        hr = max(50, min(120, base_hr + random.randint(-8, 8)))
        sys_bp = max(90, min(160, base_sys + random.randint(-10, 10)))
        dia_bp = max(55, min(100, base_dia + random.randint(-8, 8)))
        bp_text = f"{sys_bp}/{dia_bp}"
        sleep = max(3.0, min(10.0, round(base_sleep + random.uniform(-1.5, 1.5), 1)))
        weight = round(base_weight + random.uniform(-0.5, 0.5), 1)
        mood = random.choices([1, 2, 3, 4, 5], weights=[3, 10, 30, 40, 17])[0]
        energy = random.choices([1, 2, 3, 4, 5], weights=[3, 8, 30, 42, 17])[0]
        water = random.randint(800, 2500)
        steps = random.randint(1500, 12000)
        note = random.choice([
            '', 'Hom nay cam thay kha tot.', 'Ngay binh thuong.',
            'Ngu khong tot dem qua.', 'Tap gym 45 phut.',
            'Uong du nuoc, an uong lanh manh.', 'Hoi met vi lam viec nhieu.',
            'Di dao buoi sang 30 phut.', 'An sang day du, ngu som.',
        ])

        rows.append((
            benh_nhan_id, d.isoformat(), hr, sys_bp, dia_bp, bp_text,
            sleep, weight, mood, energy, water, steps, note,
        ))
    return rows


def gen_mood_entries(benh_nhan_id: int, days: int = 14) -> list[tuple]:
    """Tạo nhật ký tâm trạng AI."""
    rows = []
    today = date.today()

    contents = [
        ('Hom nay rat vui, di lam suon se, gap ban be buoi toi.', 'tap yoga, doc sach'),
        ('Cam thay binh thuong, ngay lam viec nhu moi ngay.', 'lam viec, nau an'),
        ('Hoi met vi it ngu, nhung van co the lam viec duoc.', 'lam viec, xem phim'),
        ('Rat hanh phuc vi hoan thanh du an quan trong!', 'lam viec, an mung'),
        ('Buon vi mat do quan trong.', 'o nha, nghe nhac'),
        ('Cam thay thoai mai sau khi tap the duc buoi sang.', 'chay bo, tap gym'),
        ('Ngay binh thuong, khong co gi dac biet.', 'lam viec, nau an'),
        ('Hao hung voi ke hoach du lich cuoi tuan.', 'len ke hoach, mua sam'),
        ('Hoi lo lang ve suc khoe, can di kham.', 'nghi ngoi, doc sach'),
        ('Tuyet voi! Duoc tang luong va khen thuong.', 'lam viec, an mung'),
        ('Cam thay co don vi o nha mot minh ca ngay.', 'xem phim, nau an'),
        ('Vui ve khi duoc gap gia dinh vao cuoi tuan.', 'di choi, an uong'),
        ('Binh thuong, tap trung lam viec.', 'lam viec, tap the duc'),
        ('Cam thay tot hon sau khi ngu du giac.', 'nghi ngoi, yoga'),
    ]

    sentiments = {
        5: 'Tich cuc ✨', 4: 'Tich cuc ✨', 3: 'On dinh 🌤️',
        2: 'Can chu y 💛', 1: 'Can ho tro 🆘',
    }
    tips = [
        '🌟 Tuyet voi! Hay chia se nang luong tich cuc nay.',
        '🌿 Hay danh 15 phut di dao ngoai troi.',
        '🥗 Mot bua an lanh manh co the cai thien tam trang.',
        '💛 Hay nho rang moi cam xuc deu tam thoi.',
        '🧘 Thien 5 phut de duy tri trang thai can bang.',
        '📚 Doc mot vai trang sach truyen cam hung.',
        '💧 Uong du nuoc giup duy tri nang luong.',
    ]

    for i in range(days):
        d = today - timedelta(days=days - 1 - i)
        mood_level = random.choices([1, 2, 3, 4, 5], weights=[3, 10, 30, 40, 17])[0]
        content, activity = contents[i % len(contents)]
        sleep_score = random.randint(2, 5)
        energy_score = random.randint(2, 5)
        sentiment = sentiments.get(mood_level, 'On dinh 🌤️')
        tip = random.choice(tips)

        rows.append((
            benh_nhan_id, d.isoformat(), mood_level, content, activity,
            sleep_score, energy_score, sentiment, tip,
        ))
    return rows


def gen_diagnosis_logs(benh_nhan_id: int, nguoi_dung_id: int, count: int = 5) -> list[tuple]:
    """Tạo lịch sử chẩn đoán AI mẫu."""
    samples = [
        {
            'text': 'Dau dau, chong mat, met moi',
            'symptoms': [
                {'id': 'dau-dau', 'label': 'Đau đầu'},
                {'id': 'chong-mat', 'label': 'Chóng mặt'},
            ],
            'result': {
                'risk_level': 'medium',
                'results': [
                    {'name': 'Thiếu máu não', 'confidence': 62, 'specialist': 'Thần kinh'},
                    {'name': 'Hạ huyết áp', 'confidence': 48, 'specialist': 'Tim mạch'},
                ],
                'advice': 'Nen dat lich voi bac si Than kinh de duoc kham truc tiep.',
            },
            'risk': 'medium',
        },
        {
            'text': 'Ho khan keo dai, kho tho nhe',
            'symptoms': [
                {'id': 'ho', 'label': 'Ho'},
                {'id': 'kho-tho', 'label': 'Khó thở'},
            ],
            'result': {
                'risk_level': 'medium',
                'results': [
                    {'name': 'Viêm phế quản', 'confidence': 55, 'specialist': 'Hô hấp'},
                    {'name': 'Hen suyễn', 'confidence': 40, 'specialist': 'Hô hấp'},
                ],
                'advice': 'Theo doi them, dat lich kham neu ho keo dai tren 2 tuan.',
            },
            'risk': 'medium',
        },
        {
            'text': 'Dau bung, buon non, tieu chay',
            'symptoms': [
                {'id': 'dau-bung', 'label': 'Đau bụng'},
                {'id': 'buon-non', 'label': 'Buồn nôn'},
            ],
            'result': {
                'risk_level': 'low',
                'results': [
                    {'name': 'Ngộ độc thực phẩm', 'confidence': 45, 'specialist': 'Tiêu hóa'},
                    {'name': 'Viêm dạ dày', 'confidence': 38, 'specialist': 'Tiêu hóa'},
                ],
                'advice': 'Theo doi them, nghi ngoi va uong nhieu nuoc.',
            },
            'risk': 'low',
        },
        {
            'text': 'Sot cao, dau co, nhuc dau',
            'symptoms': [
                {'id': 'sot', 'label': 'Sốt'},
                {'id': 'dau-co', 'label': 'Đau cơ'},
            ],
            'result': {
                'risk_level': 'high',
                'results': [
                    {'name': 'Sốt xuất huyết', 'confidence': 72, 'specialist': 'Truyền nhiễm'},
                    {'name': 'Cúm', 'confidence': 55, 'specialist': 'Nội tổng quát'},
                ],
                'advice': 'Nen lien he co so y te som, dac biet neu sot keo dai.',
            },
            'risk': 'high',
        },
        {
            'text': 'Ngua da, noi man do, phat ban',
            'symptoms': [
                {'id': 'ngua', 'label': 'Ngứa da'},
                {'id': 'phat-ban', 'label': 'Phát ban'},
            ],
            'result': {
                'risk_level': 'low',
                'results': [
                    {'name': 'Dị ứng da', 'confidence': 65, 'specialist': 'Da liễu'},
                    {'name': 'Mề đay', 'confidence': 50, 'specialist': 'Da liễu'},
                ],
                'advice': 'Co the dat lich voi bac si Da lieu de duoc kham.',
            },
            'risk': 'low',
        },
        {
            'text': 'Mat mo, nhin doi, dau mat',
            'symptoms': [
                {'id': 'dau-mat', 'label': 'Đau mắt'},
                {'id': 'mo-mat', 'label': 'Mờ mắt'},
            ],
            'result': {
                'risk_level': 'medium',
                'results': [
                    {'name': 'Cận thị tiến triển', 'confidence': 58, 'specialist': 'Mắt'},
                    {'name': 'Viêm kết mạc', 'confidence': 42, 'specialist': 'Mắt'},
                ],
                'advice': 'Nen dat lich voi bac si Mat de kiem tra thi luc.',
            },
            'risk': 'medium',
        },
        {
            'text': 'Dau lung, cung co, kho cu dong',
            'symptoms': [
                {'id': 'dau-lung', 'label': 'Đau lưng'},
                {'id': 'cung-co', 'label': 'Cứng cơ'},
            ],
            'result': {
                'risk_level': 'low',
                'results': [
                    {'name': 'Thoái hóa cột sống', 'confidence': 50, 'specialist': 'Cơ xương khớp'},
                    {'name': 'Đau cơ do vận động', 'confidence': 45, 'specialist': 'Phục hồi chức năng'},
                ],
                'advice': 'Nghi ngoi, tap bai tap gian co nhe nhang.',
            },
            'risk': 'low',
        },
    ]

    rows = []
    today = date.today()
    for i in range(count):
        sample = samples[i % len(samples)]
        d = today - timedelta(days=count - i)
        ngay_tao = f"{d.isoformat()} {random.randint(8,20):02d}:{random.randint(0,59):02d}:00"
        rows.append((
            benh_nhan_id,
            nguoi_dung_id,
            sample['text'],
            json.dumps(sample['symptoms'], ensure_ascii=False),
            json.dumps(sample['result'], ensure_ascii=False),
            sample['risk'],
            ngay_tao,
        ))
    return rows


# ─── Main ──────────────────────────────────────────────────────────────

def main():
    conn = get_connection()
    cursor = conn.cursor()
    print("[SEED] Bat dau tao du lieu mau cho module suc khoe...")

    # Đảm bảo bảng đã tồn tại (gọi schema service logic)
    _ensure_tables(cursor, conn)

    # Mapping benh_nhan_id -> nguoi_dung_id (lấy từ DB)
    cursor.execute("SELECT id, nguoi_dung_id FROM benh_nhan ORDER BY id LIMIT 10")
    patients = cursor.fetchall()
    if not patients:
        print("[WARN] Khong co benh nhan nao trong database.")
        return

    total_health = 0
    total_mood = 0
    total_diag = 0

    for bn_id, nd_id in patients:
        # 1. Health logs - 30 ngày
        health_rows = gen_health_logs(bn_id, days=30)
        for row in health_rows:
            try:
                cursor.execute("""
                    INSERT INTO suc_khoe_log
                    (benh_nhan_id, ngay, nhip_tim, huyet_ap_tam_thu, huyet_ap_tam_truong,
                     huyet_ap, giac_ngu, can_nang, tam_trang, muc_nang_luong, nuoc_uong,
                     buoc_di, ghi_chu)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        nhip_tim = VALUES(nhip_tim),
                        huyet_ap_tam_thu = VALUES(huyet_ap_tam_thu),
                        huyet_ap_tam_truong = VALUES(huyet_ap_tam_truong),
                        huyet_ap = VALUES(huyet_ap),
                        giac_ngu = VALUES(giac_ngu),
                        can_nang = VALUES(can_nang),
                        tam_trang = VALUES(tam_trang),
                        muc_nang_luong = VALUES(muc_nang_luong),
                        nuoc_uong = VALUES(nuoc_uong),
                        buoc_di = VALUES(buoc_di),
                        ghi_chu = VALUES(ghi_chu)
                """, row)
                total_health += 1
            except Exception as e:
                print(f"  [WARN] suc_khoe_log BN#{bn_id}: {e}")

        # 2. Mood journal - 14 ngày
        mood_rows = gen_mood_entries(bn_id, days=14)
        for row in mood_rows:
            try:
                cursor.execute("""
                    INSERT INTO nhat_ky_tam_trang
                    (benh_nhan_id, ngay, muc_tam_trang, noi_dung, hoat_dong,
                     giac_ngu_diem, nang_luong_diem, ai_phan_tich, ai_goi_y)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        muc_tam_trang = VALUES(muc_tam_trang),
                        noi_dung = VALUES(noi_dung),
                        hoat_dong = VALUES(hoat_dong),
                        giac_ngu_diem = VALUES(giac_ngu_diem),
                        nang_luong_diem = VALUES(nang_luong_diem),
                        ai_phan_tich = VALUES(ai_phan_tich),
                        ai_goi_y = VALUES(ai_goi_y)
                """, row)
                total_mood += 1
            except Exception as e:
                print(f"  [WARN] nhat_ky_tam_trang BN#{bn_id}: {e}")

        # 3. AI Diagnosis history - 5 lần
        diag_rows = gen_diagnosis_logs(bn_id, nd_id, count=5)
        for row in diag_rows:
            try:
                cursor.execute("""
                    INSERT INTO ai_chan_doan_log
                    (benh_nhan_id, nguoi_dung_id, trieu_chung_text, trieu_chung_json,
                     ket_qua_json, muc_nguy_co, ngay_tao)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, row)
                total_diag += 1
            except Exception as e:
                print(f"  [WARN] ai_chan_doan_log BN#{bn_id}: {e}")

        print(f"  [OK] BN#{bn_id} (ND#{nd_id}): health={len(health_rows)}, mood={len(mood_rows)}, diag={len(diag_rows)}")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n[DONE] Da tao du lieu mau:")
    print(f"  - suc_khoe_log: {total_health} rows")
    print(f"  - nhat_ky_tam_trang: {total_mood} rows")
    print(f"  - ai_chan_doan_log: {total_diag} rows")
    print(f"\n[INFO] Dang nhap vao http://localhost:5000 va mo Tien ich suc khoe de xem ket qua.")


def _ensure_tables(cursor, conn):
    """Tạo các bảng nếu chưa tồn tại."""
    tables = [
        """
        CREATE TABLE IF NOT EXISTS suc_khoe_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            benh_nhan_id INT NOT NULL,
            ngay DATE NOT NULL,
            nhip_tim INT DEFAULT NULL,
            huyet_ap_tam_thu INT DEFAULT NULL,
            huyet_ap_tam_truong INT DEFAULT NULL,
            huyet_ap VARCHAR(10) DEFAULT NULL,
            giac_ngu DECIMAL(4,1) DEFAULT NULL,
            can_nang DECIMAL(5,1) DEFAULT NULL,
            tam_trang INT DEFAULT 3,
            muc_nang_luong INT DEFAULT 3,
            nuoc_uong INT DEFAULT 0,
            buoc_di INT DEFAULT 0,
            ghi_chu TEXT,
            ngay_tao DATETIME DEFAULT CURRENT_TIMESTAMP,
            ngay_cap_nhat DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_suc_khoe_ngay (benh_nhan_id, ngay),
            INDEX idx_suc_khoe_benh_nhan (benh_nhan_id),
            INDEX idx_suc_khoe_ngay (ngay)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS nhat_ky_tam_trang (
            id INT AUTO_INCREMENT PRIMARY KEY,
            benh_nhan_id INT NOT NULL,
            ngay DATE NOT NULL,
            muc_tam_trang TINYINT NOT NULL DEFAULT 3,
            noi_dung TEXT,
            hoat_dong VARCHAR(500),
            giac_ngu_diem TINYINT DEFAULT 3,
            nang_luong_diem TINYINT DEFAULT 3,
            ai_phan_tich VARCHAR(100),
            ai_goi_y TEXT,
            ngay_tao DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_mood_ngay (benh_nhan_id, ngay),
            INDEX idx_mood_benh_nhan (benh_nhan_id),
            INDEX idx_mood_ngay (ngay)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS ai_chan_doan_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            benh_nhan_id INT DEFAULT NULL,
            nguoi_dung_id INT DEFAULT NULL,
            trieu_chung_text TEXT,
            trieu_chung_json JSON,
            ket_qua_json JSON,
            muc_nguy_co VARCHAR(30),
            ngay_tao DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_ai_cd_benh_nhan (benh_nhan_id),
            INDEX idx_ai_cd_nguoi_dung (nguoi_dung_id),
            INDEX idx_ai_cd_ngay (ngay_tao)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
    ]
    for sql in tables:
        cursor.execute(sql)
    conn.commit()
    print("[OK] Dam bao cac bang tien ich da ton tai.")


if __name__ == '__main__':
    main()
