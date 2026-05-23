"""
Admin Controller - dashboard, quan ly bac si, benh nhan, lich kham
va kho du lieu cho module Tien ich suc khoe.
"""
from flask import Blueprint, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash

from core.controller import BaseController
from core.middleware import login_required, role_required
from core.database import db
from app.models.nguoi_dung_model import NguoiDungModel
from app.models.bac_si_model import BacSiModel
from app.models.benh_nhan_model import BenhNhanModel
from app.models.lich_kham_model import LichKhamModel
from app.models.thanh_toan_model import ThanhToanModel
from app.models.chuyen_khoa_model import ChuyenKhoaModel
from app.services.health_data_repository import HealthDataRepository
from app.services.utility_schema_service import UtilitySchemaService


admin_bp = Blueprint('admin', __name__)


# ─── Helpers ────────────────────────────────────────────────────────────────

def thong_ke_tien_ich():
    stats = {
        'health_logs': 0,
        'mood_entries': 0,
        'mood_this_week': 0,
        'ai_diagnosis': 0,
    }
    if not UtilitySchemaService.ensure():
        return stats
    try:
        stats['health_logs'] = db.count('suc_khoe_log')
        stats['mood_entries'] = db.count('nhat_ky_tam_trang')
        stats['mood_this_week'] = db.count('nhat_ky_tam_trang', 'ngay >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)')
        stats['ai_diagnosis'] = db.count('ai_chan_doan_log')
    except Exception:
        pass
    return stats


# ═══════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    """Dashboard admin tong quan."""
    thong_ke = {
        'nguoi_dung_moi': NguoiDungModel.count("ngay_tao >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"),
        'lich_hoan_thanh': LichKhamModel.count("trang_thai = 'hoan_thanh'"),
        'doanh_thu': ThanhToanModel.doanh_thu_thang(),
        'cho_duyet': BacSiModel.count("trang_thai_duyet = 'cho_duyet'"),
        'tong_bac_si': BacSiModel.count("trang_thai_duyet = 'da_duyet'"),
        'tong_benh_nhan': db.count('benh_nhan'),
    }
    thong_ke_ck = LichKhamModel.thong_ke_theo_chuyen_khoa()
    bs_cho_duyet = BacSiModel.cho_duyet()
    hoat_dong = db.query("""
        SELECT ls.*, nd.ho_ten
        FROM lich_su ls
        LEFT JOIN nguoi_dung nd ON ls.nguoi_dung_id = nd.id
        ORDER BY ls.ngay_tao DESC
        LIMIT 10
    """)

    return BaseController.render(
        'admin/dashboard.html',
        thong_ke=thong_ke,
        thong_ke_ck=thong_ke_ck,
        bs_cho_duyet=bs_cho_duyet,
        hoat_dong=hoat_dong,
        tien_ich_stats=thong_ke_tien_ich(),
        data_stats=HealthDataRepository.stats(),
    )


# ═══════════════════════════════════════════════════════════════════
# QUẢN LÝ BÁC SĨ  (Read / Approve / Reject / Edit / Delete)
# ═══════════════════════════════════════════════════════════════════

@admin_bp.route('/bac-si')
@login_required
@role_required('admin')
def quan_ly_bac_si():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '')
    result = BacSiModel.tim_bac_si(search=search, page=page, per_page=10)
    chuyen_khoa_list = ChuyenKhoaModel.lay_tat_ca_hoat_dong()
    return BaseController.render(
        'admin/quan_ly_bac_si.html',
        result=result,
        search=search,
        chuyen_khoa_list=chuyen_khoa_list,
    )


@admin_bp.route('/bac-si/duyet/<int:bac_si_id>/<trang_thai>', methods=['POST'])
@login_required
@role_required('admin')
def duyet_bac_si(bac_si_id, trang_thai):
    if trang_thai in ('da_duyet', 'tu_choi'):
        BacSiModel.duyet_bac_si(bac_si_id, trang_thai)
        msg = 'đã duyệt' if trang_thai == 'da_duyet' else 'đã từ chối'
        flash(f'Hồ sơ bác sĩ {msg}.', 'success')
    return redirect(url_for('admin.quan_ly_bac_si'))


@admin_bp.route('/bac-si/duyet-tat-ca', methods=['POST'])
@login_required
@role_required('admin')
def duyet_tat_ca_bac_si():
    """Duyệt tất cả bác sĩ đang chờ."""
    bs_list = BacSiModel.cho_duyet()
    count = 0
    for bs in bs_list:
        BacSiModel.duyet_bac_si(bs['id'], 'da_duyet')
        count += 1
    flash(f'Đã duyệt {count} bác sĩ.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/bac-si/sua/<int:bac_si_id>', methods=['POST'])
@login_required
@role_required('admin')
def sua_bac_si(bac_si_id):
    """Cập nhật thông tin bác sĩ từ admin."""
    data = {}
    if request.form.get('benh_vien'):
        data['benh_vien'] = request.form['benh_vien'].strip()
    if request.form.get('kinh_nghiem'):
        data['kinh_nghiem'] = int(request.form['kinh_nghiem'])
    if request.form.get('gia_kham'):
        data['gia_kham'] = int(request.form['gia_kham'])
    if request.form.get('chuyen_khoa_id'):
        data['chuyen_khoa_id'] = int(request.form['chuyen_khoa_id'])

    if data:
        BacSiModel.update(bac_si_id, data)

    # Cập nhật tên trong bảng nguoi_dung
    bs = BacSiModel.get_by_id(bac_si_id)
    if bs and request.form.get('ho_ten'):
        NguoiDungModel.update(bs['nguoi_dung_id'], {
            'ho_ten': request.form['ho_ten'].strip()
        })

    flash('Đã cập nhật thông tin bác sĩ.', 'success')
    return redirect(url_for('admin.quan_ly_bac_si'))


@admin_bp.route('/bac-si/xoa/<int:bac_si_id>', methods=['POST'])
@login_required
@role_required('admin')
def xoa_bac_si(bac_si_id):
    """Xóa bác sĩ (xóa cả tài khoản nguoi_dung)."""
    bs = BacSiModel.get_by_id(bac_si_id)
    if bs:
        # Xóa bác sĩ trước (FK cascade sẽ xóa lich_kham liên quan)
        BacSiModel.delete(bac_si_id)
        # Xóa tài khoản người dùng
        NguoiDungModel.delete(bs['nguoi_dung_id'])
        flash('Đã xóa bác sĩ khỏi hệ thống.', 'success')
    else:
        flash('Không tìm thấy bác sĩ.', 'danger')
    return redirect(url_for('admin.quan_ly_bac_si'))


# ═══════════════════════════════════════════════════════════════════
# QUẢN LÝ BỆNH NHÂN  (Read / Edit / Delete)
# ═══════════════════════════════════════════════════════════════════

@admin_bp.route('/benh-nhan')
@login_required
@role_required('admin')
def quan_ly_benh_nhan():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '')
    result = BenhNhanModel.danh_sach_benh_nhan(page=page, search=search)
    return BaseController.render('admin/quan_ly_benh_nhan.html', result=result, search=search)


@admin_bp.route('/benh-nhan/sua/<int:benh_nhan_id>', methods=['POST'])
@login_required
@role_required('admin')
def sua_benh_nhan(benh_nhan_id):
    """Cập nhật thông tin bệnh nhân."""
    bn = BenhNhanModel.get_by_id(benh_nhan_id)
    if not bn:
        flash('Không tìm thấy bệnh nhân.', 'danger')
        return redirect(url_for('admin.quan_ly_benh_nhan'))

    # Cập nhật bảng benh_nhan
    bn_data = {}
    for field in ('ngay_sinh', 'gioi_tinh', 'dia_chi', 'nhom_mau', 'huyet_ap'):
        val = request.form.get(field)
        if val is not None:
            bn_data[field] = val.strip() if val else None
    for field in ('chieu_cao', 'can_nang', 'nhip_tim'):
        val = request.form.get(field)
        if val:
            try:
                bn_data[field] = float(val)
            except ValueError:
                pass
    if bn_data:
        BenhNhanModel.update(benh_nhan_id, bn_data)

    # Cập nhật bảng nguoi_dung (tên, SĐT)
    nd_data = {}
    if request.form.get('ho_ten'):
        nd_data['ho_ten'] = request.form['ho_ten'].strip()
    if request.form.get('so_dien_thoai'):
        nd_data['so_dien_thoai'] = request.form['so_dien_thoai'].strip()
    if nd_data:
        NguoiDungModel.update(bn['nguoi_dung_id'], nd_data)

    flash('Đã cập nhật thông tin bệnh nhân.', 'success')
    return redirect(url_for('admin.quan_ly_benh_nhan'))


@admin_bp.route('/benh-nhan/xoa/<int:benh_nhan_id>', methods=['POST'])
@login_required
@role_required('admin')
def xoa_benh_nhan(benh_nhan_id):
    """Xóa bệnh nhân (xóa cả tài khoản nguoi_dung)."""
    bn = BenhNhanModel.get_by_id(benh_nhan_id)
    if bn:
        BenhNhanModel.delete(benh_nhan_id)
        NguoiDungModel.delete(bn['nguoi_dung_id'])
        flash('Đã xóa bệnh nhân khỏi hệ thống.', 'success')
    else:
        flash('Không tìm thấy bệnh nhân.', 'danger')
    return redirect(url_for('admin.quan_ly_benh_nhan'))


# ═══════════════════════════════════════════════════════════════════
# QUẢN LÝ LỊCH KHÁM  (Read / Cancel / Confirm / Detail)
# ═══════════════════════════════════════════════════════════════════

@admin_bp.route('/lich-kham')
@login_required
@role_required('admin')
def quan_ly_lich():
    page = request.args.get('page', 1, type=int)
    trang_thai = request.args.get('trang_thai', '')
    per_page = 20

    where = "1=1"
    params = []
    if trang_thai:
        where = "lk.trang_thai = %s"
        params.append(trang_thai)

    # Đếm tổng — dùng parameterized query
    count_sql = f"""
        SELECT COUNT(*) as total
        FROM lich_kham lk
        WHERE {where}
    """
    total_row = db.get_one(count_sql, tuple(params))
    total = total_row['total'] if total_row else 0
    total_pages = max(1, (total + per_page - 1) // per_page)

    offset = (page - 1) * per_page
    sql = f"""
        SELECT lk.*, nd_bn.ho_ten as ten_benh_nhan, bn.ma_benh_nhan,
               nd_bs.ho_ten as ten_bac_si, bs.hoc_vi,
               ck.ten_chuyen_khoa
        FROM lich_kham lk
        JOIN benh_nhan bn ON lk.benh_nhan_id = bn.id
        JOIN nguoi_dung nd_bn ON bn.nguoi_dung_id = nd_bn.id
        JOIN bac_si bs ON lk.bac_si_id = bs.id
        JOIN nguoi_dung nd_bs ON bs.nguoi_dung_id = nd_bs.id
        JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
        WHERE {where}
        ORDER BY lk.ngay_kham DESC, lk.gio_kham DESC
        LIMIT %s OFFSET %s
    """
    lich_list = db.query(sql, tuple(params) + (per_page, offset))

    return BaseController.render(
        'admin/quan_ly_lich.html',
        lich_list=lich_list,
        trang_thai=trang_thai,
        page=page,
        total=total,
        total_pages=total_pages,
    )


@admin_bp.route('/lich-kham/huy/<int:lich_id>', methods=['POST'])
@login_required
@role_required('admin')
def huy_lich(lich_id):
    LichKhamModel.cap_nhat_trang_thai(lich_id, 'da_huy')
    flash('Đã hủy lịch khám.', 'success')
    return redirect(url_for('admin.quan_ly_lich'))


@admin_bp.route('/lich-kham/xac-nhan/<int:lich_id>', methods=['POST'])
@login_required
@role_required('admin')
def xac_nhan_lich(lich_id):
    """Admin xác nhận lịch khám thay bác sĩ."""
    LichKhamModel.cap_nhat_trang_thai(lich_id, 'da_xac_nhan')
    flash('Đã xác nhận lịch khám.', 'success')
    return redirect(url_for('admin.quan_ly_lich'))


# ═══════════════════════════════════════════════════════════════════
# API THỐNG KÊ
# ═══════════════════════════════════════════════════════════════════

@admin_bp.route('/api/thong-ke')
@login_required
@role_required('admin')
def api_thong_ke():
    thong_ke_ck = LichKhamModel.thong_ke_theo_chuyen_khoa()
    return BaseController.json_response({
        'chuyen_khoa': [
            {'ten': tk['ten_chuyen_khoa'], 'so_luong': tk['so_luong']}
            for tk in thong_ke_ck
        ],
        'tien_ich': thong_ke_tien_ich(),
        'kho_du_lieu': HealthDataRepository.stats(),
    })


# ═══════════════════════════════════════════════════════════════════
# KHO DỮ LIỆU
# ═══════════════════════════════════════════════════════════════════

@admin_bp.route('/kho-du-lieu')
@login_required
@role_required('admin')
def kho_du_lieu():
    """Xem nhanh kho food/exercise/disease va log suc khoe moi."""
    search = request.args.get('q', '').strip().lower()
    tab = request.args.get('tab', 'thuc_pham')
    nutrition = HealthDataRepository.nutrition_data()
    diagnosis = HealthDataRepository.diagnosis_data()
    foods = nutrition.get('foods', [])
    exercises = nutrition.get('exercises', [])
    diseases = diagnosis.get('diseases', [])

    if search:
        foods = [
            item for item in foods
            if search in item.get('name', '').lower() or search in item.get('group', '').lower()
        ]
        exercises = [
            item for item in exercises
            if search in item.get('name', '').lower() or search in item.get('type', '').lower()
        ]
        diseases = [
            item for item in diseases
            if search in item.get('name', '').lower() or search in item.get('specialist', '').lower()
        ]

    recent_health_logs = []
    if UtilitySchemaService.ensure():
        recent_health_logs = db.query("""
            SELECT skl.*, nd.ho_ten, bn.ma_benh_nhan
            FROM suc_khoe_log skl
            JOIN benh_nhan bn ON skl.benh_nhan_id = bn.id
            JOIN nguoi_dung nd ON bn.nguoi_dung_id = nd.id
            ORDER BY skl.ngay DESC
            LIMIT 20
        """)

    # Danh mục thuốc
    thuoc_list = []
    thuoc_total = 0
    try:
        thuoc_search = request.args.get('thuoc_q', '').strip()
        thuoc_where = "1=1"
        thuoc_params = []
        if thuoc_search:
            thuoc_where += " AND (ten_thuoc LIKE %s OR hoat_chat LIKE %s OR nhom_thuoc LIKE %s)"
            thuoc_params += [f"%{thuoc_search}%"] * 3
        thuoc_total = db.get_one(f"SELECT COUNT(*) AS c FROM danh_muc_thuoc WHERE {thuoc_where}", tuple(thuoc_params))['c']
        thuoc_list = db.query(f"""
            SELECT * FROM danh_muc_thuoc WHERE {thuoc_where}
            ORDER BY ten_thuoc ASC LIMIT 30
        """, tuple(thuoc_params))
    except Exception:
        pass

    # Nhật ký tâm trạng AI (thay thế nhắc thuốc Gmail)
    mood_list = []
    mood_stats = {}
    try:
        from app.services.mood_journal_service import MoodJournalService
        mood_list = MoodJournalService.admin_list_all(limit=25)
        mood_stats = MoodJournalService.admin_stats()
    except Exception:
        pass

    # Hoạt động gần đây
    hoat_dong = []
    try:
        hoat_dong = db.query("""
            SELECT nd.ho_ten, nd.vai_tro, nd.lan_dang_nhap_cuoi, nd.email
            FROM nguoi_dung nd
            WHERE nd.lan_dang_nhap_cuoi IS NOT NULL
            ORDER BY nd.lan_dang_nhap_cuoi DESC
            LIMIT 20
        """)
    except Exception:
        pass

    data_stats = HealthDataRepository.stats()

    return BaseController.render(
        'admin/kho_du_lieu.html',
        foods=foods,
        exercises=exercises,
        diseases=diseases,
        stats=data_stats,
        search=search,
        tab=tab,
        recent_health_logs=recent_health_logs,
        thuoc_list=thuoc_list,
        thuoc_total=thuoc_total,
        thuoc_search=request.args.get('thuoc_q', ''),
        mood_list=mood_list,
        mood_stats=mood_stats,
        hoat_dong=hoat_dong,
    )


@admin_bp.route('/api/thuoc/them', methods=['POST'])
@login_required
@role_required('admin')
def api_them_thuoc():
    """Thêm thuốc mới vào danh mục."""
    data = request.get_json(silent=True) or {}
    ten = data.get('ten_thuoc', '').strip()
    if not ten:
        return BaseController.json_error('Tên thuốc không được trống.', status=400)
    db.execute("""
        INSERT INTO danh_muc_thuoc (ten_thuoc, hoat_chat, nhom_thuoc, don_vi, hang_san_xuat, mo_ta)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (ten, data.get('hoat_chat',''), data.get('nhom_thuoc',''),
          data.get('don_vi','viên'), data.get('hang_san_xuat',''), data.get('mo_ta','')))
    return BaseController.json_response(message='Đã thêm thuốc mới.')


@admin_bp.route('/api/thuoc/sua/<int:thuoc_id>', methods=['POST'])
@login_required
@role_required('admin')
def api_sua_thuoc(thuoc_id):
    """Sửa thông tin thuốc."""
    data = request.get_json(silent=True) or {}
    fields = {}
    for f in ('ten_thuoc','hoat_chat','nhom_thuoc','don_vi','hang_san_xuat','mo_ta'):
        if f in data:
            fields[f] = data[f]
    if not fields:
        return BaseController.json_error('Không có dữ liệu.', status=400)
    sets = ', '.join(f"{k}=%s" for k in fields)
    vals = list(fields.values()) + [thuoc_id]
    db.execute(f"UPDATE danh_muc_thuoc SET {sets} WHERE id=%s", tuple(vals))
    return BaseController.json_response(message='Đã cập nhật thuốc.')


@admin_bp.route('/api/thuoc/xoa/<int:thuoc_id>', methods=['POST'])
@login_required
@role_required('admin')
def api_xoa_thuoc(thuoc_id):
    """Xóa thuốc khỏi danh mục."""
    db.execute("DELETE FROM danh_muc_thuoc WHERE id=%s", (thuoc_id,))
    return BaseController.json_response(message='Đã xóa thuốc.')


# ── CRUD Thực phẩm / Bài tập / Bệnh (JSON files) ──────────────────

def _load_json(filename):
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "data" / filename
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _save_json(filename, data):
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "data" / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # Clear lru_cache
    HealthDataRepository._load_json.cache_clear()


@admin_bp.route('/api/kho-du-lieu/food', methods=['POST'])
@login_required
@role_required('admin')
def api_crud_food():
    """Thêm/Sửa thực phẩm trong JSON."""
    payload = request.get_json(silent=True) or {}
    data = _load_json("health_knowledge.json")
    foods = data.get("foods", [])
    idx = payload.get("index", -1)
    item = {
        "name": payload.get("name", ""),
        "group": payload.get("group", ""),
        "calories": payload.get("calories", 0),
        "protein": payload.get("protein", 0),
        "fat": payload.get("fat", 0),
        "goal": payload.get("goal", []),
    }
    if not item["name"]:
        return BaseController.json_error("Tên không được trống.", status=400)
    if 0 <= idx < len(foods):
        item["goal"] = foods[idx].get("goal", [])
        foods[idx] = item
        msg = "Đã cập nhật thực phẩm."
    else:
        foods.append(item)
        msg = "Đã thêm thực phẩm mới."
    data["foods"] = foods
    _save_json("health_knowledge.json", data)
    return BaseController.json_response(message=msg)


@admin_bp.route('/api/kho-du-lieu/food/xoa', methods=['POST'])
@login_required
@role_required('admin')
def api_xoa_food():
    payload = request.get_json(silent=True) or {}
    idx = payload.get("index", -1)
    data = _load_json("health_knowledge.json")
    foods = data.get("foods", [])
    if 0 <= idx < len(foods):
        foods.pop(idx)
        data["foods"] = foods
        _save_json("health_knowledge.json", data)
        return BaseController.json_response(message="Đã xóa thực phẩm.")
    return BaseController.json_error("Không tìm thấy.", status=404)


@admin_bp.route('/api/kho-du-lieu/exercise', methods=['POST'])
@login_required
@role_required('admin')
def api_crud_exercise():
    payload = request.get_json(silent=True) or {}
    data = _load_json("health_knowledge.json")
    exercises = data.get("exercises", [])
    idx = payload.get("index", -1)
    item = {
        "name": payload.get("name", ""),
        "type": payload.get("type", ""),
        "level": payload.get("level", ""),
        "minutes": payload.get("minutes", 0),
        "goal": payload.get("goal", []),
    }
    if not item["name"]:
        return BaseController.json_error("Tên không được trống.", status=400)
    if 0 <= idx < len(exercises):
        item["goal"] = exercises[idx].get("goal", [])
        exercises[idx] = item
        msg = "Đã cập nhật bài tập."
    else:
        exercises.append(item)
        msg = "Đã thêm bài tập mới."
    data["exercises"] = exercises
    _save_json("health_knowledge.json", data)
    return BaseController.json_response(message=msg)


@admin_bp.route('/api/kho-du-lieu/exercise/xoa', methods=['POST'])
@login_required
@role_required('admin')
def api_xoa_exercise():
    payload = request.get_json(silent=True) or {}
    idx = payload.get("index", -1)
    data = _load_json("health_knowledge.json")
    exercises = data.get("exercises", [])
    if 0 <= idx < len(exercises):
        exercises.pop(idx)
        data["exercises"] = exercises
        _save_json("health_knowledge.json", data)
        return BaseController.json_response(message="Đã xóa bài tập.")
    return BaseController.json_error("Không tìm thấy.", status=404)


@admin_bp.route('/api/kho-du-lieu/disease', methods=['POST'])
@login_required
@role_required('admin')
def api_crud_disease():
    payload = request.get_json(silent=True) or {}
    data = _load_json("symptom_disease_dataset.json")
    diseases = data.get("diseases", [])
    idx = payload.get("index", -1)
    item = {
        "name": payload.get("name", ""),
        "specialist": payload.get("specialist", ""),
        "description": payload.get("description", ""),
        "red_flags": payload.get("red_flags", []),
        "symptoms": payload.get("symptoms", {}),
        "advice": payload.get("advice", ""),
    }
    if not item["name"]:
        return BaseController.json_error("Tên không được trống.", status=400)
    if 0 <= idx < len(diseases):
        item["symptoms"] = diseases[idx].get("symptoms", {})
        item["advice"] = diseases[idx].get("advice", item["advice"])
        item["id"] = diseases[idx].get("id", item["name"].lower().replace(" ", "-"))
        diseases[idx] = item
        msg = "Đã cập nhật bệnh."
    else:
        item["id"] = item["name"].lower().replace(" ", "-")
        diseases.append(item)
        msg = "Đã thêm bệnh mới."
    data["diseases"] = diseases
    _save_json("symptom_disease_dataset.json", data)
    return BaseController.json_response(message=msg)


@admin_bp.route('/api/kho-du-lieu/disease/xoa', methods=['POST'])
@login_required
@role_required('admin')
def api_xoa_disease():
    payload = request.get_json(silent=True) or {}
    idx = payload.get("index", -1)
    data = _load_json("symptom_disease_dataset.json")
    diseases = data.get("diseases", [])
    if 0 <= idx < len(diseases):
        diseases.pop(idx)
        data["diseases"] = diseases
        _save_json("symptom_disease_dataset.json", data)
        return BaseController.json_response(message="Đã xóa bệnh.")
    return BaseController.json_error("Không tìm thấy.", status=404)


# ═══════════════════════════════════════════════════════════════════
# QUẢN LÝ TÀI KHOẢN  (CRUD admin, bác sĩ, bệnh nhân)
# ═══════════════════════════════════════════════════════════════════

@admin_bp.route('/tai-khoan')
@login_required
@role_required('admin')
def quan_ly_tai_khoan():
    """Trang quản lý tài khoản tổng hợp."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    vai_tro = request.args.get('vai_tro', '').strip()
    per_page = 20

    where = "1=1"
    params = []
    if search:
        where += " AND (nd.ho_ten LIKE %s OR nd.email LIKE %s OR nd.so_dien_thoai LIKE %s)"
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]
    if vai_tro:
        where += " AND nd.vai_tro = %s"
        params.append(vai_tro)

    total = db.get_one(
        f"SELECT COUNT(*) AS total FROM nguoi_dung nd WHERE {where}", tuple(params)
    )['total']
    total_pages = max(1, (total + per_page - 1) // per_page)
    offset = (page - 1) * per_page

    users = db.query(f"""
        SELECT nd.*,
               COALESCE(bs.ma_bac_si, bn.ma_benh_nhan, '') AS ma_ho_so,
               COALESCE(ck.ten_chuyen_khoa, '') AS ten_chuyen_khoa,
               COALESCE(bs.trang_thai_duyet, '') AS trang_thai_duyet
        FROM nguoi_dung nd
        LEFT JOIN bac_si bs ON nd.id = bs.nguoi_dung_id
        LEFT JOIN benh_nhan bn ON nd.id = bn.nguoi_dung_id
        LEFT JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
        WHERE {where}
        ORDER BY nd.id DESC
        LIMIT %s OFFSET %s
    """, tuple(params) + (per_page, offset))

    # Thống kê
    stats = {
        'tong': total,
        'admin': NguoiDungModel.dem_theo_vai_tro('admin'),
        'bac_si': NguoiDungModel.dem_theo_vai_tro('bac_si'),
        'benh_nhan': NguoiDungModel.dem_theo_vai_tro('benh_nhan'),
    }

    chuyen_khoa_list = ChuyenKhoaModel.lay_tat_ca_hoat_dong()

    return BaseController.render(
        'admin/quan_ly_tai_khoan.html',
        users=users,
        stats=stats,
        search=search,
        vai_tro=vai_tro,
        page=page,
        total=total,
        total_pages=total_pages,
        chuyen_khoa_list=chuyen_khoa_list,
    )


@admin_bp.route('/tai-khoan/them', methods=['POST'])
@login_required
@role_required('admin')
def them_tai_khoan():
    """Tạo tài khoản mới."""
    ho_ten = request.form.get('ho_ten', '').strip()
    email = request.form.get('email', '').strip()
    mat_khau = request.form.get('mat_khau', '').strip()
    so_dien_thoai = request.form.get('so_dien_thoai', '').strip()
    vai_tro = request.form.get('vai_tro', 'benh_nhan')

    if not ho_ten or not email or not mat_khau:
        flash('Vui lòng điền đầy đủ họ tên, email và mật khẩu.', 'danger')
        return redirect(url_for('admin.quan_ly_tai_khoan'))

    if NguoiDungModel.find_by('email', email):
        flash('Email đã tồn tại trong hệ thống.', 'danger')
        return redirect(url_for('admin.quan_ly_tai_khoan'))

    user_id = NguoiDungModel.tao_nguoi_dung(ho_ten, email, mat_khau, so_dien_thoai, vai_tro)
    if not user_id:
        flash('Không tạo được tài khoản.', 'danger')
        return redirect(url_for('admin.quan_ly_tai_khoan'))

    # Tạo hồ sơ tương ứng
    if vai_tro == 'bac_si':
        chuyen_khoa_id = request.form.get('chuyen_khoa_id', 1, type=int)
        benh_vien = request.form.get('benh_vien', '').strip() or 'Chưa cập nhật'
        db.execute("""
            INSERT INTO bac_si (nguoi_dung_id, ma_bac_si, chuyen_khoa_id, hoc_vi, benh_vien,
                                kinh_nghiem, gia_kham, trang_thai_duyet)
            VALUES (%s, %s, %s, 'BS', %s, 1, 200000, 'da_duyet')
        """, (user_id, f"BS-NEW-{user_id}", chuyen_khoa_id, benh_vien))
    elif vai_tro == 'benh_nhan':
        BenhNhanModel.tao_benh_nhan(user_id)

    flash(f'Đã tạo tài khoản {vai_tro} cho {ho_ten}.', 'success')
    return redirect(url_for('admin.quan_ly_tai_khoan'))


@admin_bp.route('/tai-khoan/sua/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def sua_tai_khoan(user_id):
    """Sửa tài khoản."""
    user = NguoiDungModel.get_by_id(user_id)
    if not user:
        flash('Không tìm thấy tài khoản.', 'danger')
        return redirect(url_for('admin.quan_ly_tai_khoan'))

    nd_data = {}
    if request.form.get('ho_ten'):
        nd_data['ho_ten'] = request.form['ho_ten'].strip()
    if request.form.get('so_dien_thoai') is not None:
        nd_data['so_dien_thoai'] = request.form['so_dien_thoai'].strip()
    if request.form.get('vai_tro'):
        nd_data['vai_tro'] = request.form['vai_tro']

    # Cập nhật email nếu có thay đổi
    new_email = request.form.get('email', '').strip().lower()
    if new_email and new_email != user.get('email', ''):
        existing = db.get_one(
            "SELECT id FROM nguoi_dung WHERE email = %s AND id != %s",
            (new_email, user_id)
        )
        if existing:
            flash('Email đã được sử dụng bởi tài khoản khác.', 'danger')
            return redirect(url_for('admin.quan_ly_tai_khoan'))
        nd_data['email'] = new_email

    # Reset mật khẩu nếu có nhập
    mat_khau_moi = request.form.get('mat_khau_moi', '').strip()
    if mat_khau_moi:
        nd_data['mat_khau_hash'] = generate_password_hash(mat_khau_moi, method='pbkdf2:sha256')

    if nd_data:
        NguoiDungModel.update(user_id, nd_data)

    flash('Đã cập nhật tài khoản.', 'success')
    return redirect(url_for('admin.quan_ly_tai_khoan'))


@admin_bp.route('/tai-khoan/toggle/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def toggle_tai_khoan(user_id):
    """Khóa/Mở khóa tài khoản."""
    user = NguoiDungModel.get_by_id(user_id)
    if not user:
        flash('Không tìm thấy tài khoản.', 'danger')
        return redirect(url_for('admin.quan_ly_tai_khoan'))

    if user_id == session.get('user_id'):
        flash('Không thể khóa tài khoản của chính mình.', 'warning')
        return redirect(url_for('admin.quan_ly_tai_khoan'))

    new_status = 0 if user['trang_thai'] == 1 else 1
    NguoiDungModel.update(user_id, {'trang_thai': new_status})
    msg = 'mở khóa' if new_status == 1 else 'khóa'
    flash(f'Đã {msg} tài khoản {user["ho_ten"]}.', 'success')
    return redirect(url_for('admin.quan_ly_tai_khoan'))


@admin_bp.route('/tai-khoan/xoa/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def xoa_tai_khoan(user_id):
    """Xóa tài khoản."""
    user = NguoiDungModel.get_by_id(user_id)
    if not user:
        flash('Không tìm thấy tài khoản.', 'danger')
        return redirect(url_for('admin.quan_ly_tai_khoan'))

    if user_id == session.get('user_id'):
        flash('Không thể xóa tài khoản của chính mình.', 'warning')
        return redirect(url_for('admin.quan_ly_tai_khoan'))

    # Xóa hồ sơ liên quan trước
    if user['vai_tro'] == 'bac_si':
        bs = db.get_one("SELECT id FROM bac_si WHERE nguoi_dung_id = %s", (user_id,))
        if bs:
            BacSiModel.delete(bs['id'])
    elif user['vai_tro'] == 'benh_nhan':
        bn = db.get_one("SELECT id FROM benh_nhan WHERE nguoi_dung_id = %s", (user_id,))
        if bn:
            BenhNhanModel.delete(bn['id'])

    NguoiDungModel.delete(user_id)
    flash(f'Đã xóa tài khoản {user["ho_ten"]}.', 'success')
    return redirect(url_for('admin.quan_ly_tai_khoan'))

