"""
Bac Si Controller - dashboard, lich kham, kham benh, benh nhan cua toi, ke don.
Bỏ hồ sơ cá nhân (profile editing) => chỉ hiển thị thông tin.
"""
from __future__ import annotations

import json
import logging
from datetime import date

from flask import Blueprint, request, session, flash, redirect, url_for

from core.controller import BaseController
from core.middleware import login_required, role_required
from core.database import db
from app.models.lich_kham_model import LichKhamModel
from app.models.bac_si_model import BacSiModel
from app.models.nguoi_dung_model import NguoiDungModel
from app.models.ho_so_model import HoSoModel
from app.models.don_thuoc_model import DonThuocModel
from app.models.chuyen_khoa_model import ChuyenKhoaModel
from app.models.benh_nhan_model import BenhNhanModel
from app.models.thong_bao_model import ThongBaoModel
from app.services.consultation_service import ConsultationService
from app.services.diagnosis_service import DiagnosisService
from app.services.health_tracking_service import HealthTrackingService

logger = logging.getLogger(__name__)

bac_si_bp = Blueprint('bac_si', __name__)


# ═══════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════

@bac_si_bp.route('/dashboard')
@login_required
@role_required('bac_si')
def dashboard():
    bac_si_id = session.get('bac_si_id')
    thong_ke = LichKhamModel.thong_ke_hom_nay(bac_si_id)
    lich_hom_nay = LichKhamModel.lich_cua_bac_si(bac_si_id, ngay=date.today().isoformat())
    doanh_thu = sum(
        float(item.get('gia_kham', 0) or 0)
        for item in lich_hom_nay
        if item.get('trang_thai') in ('hoan_thanh', 'dang_kham', 'da_xac_nhan')
    ) if lich_hom_nay else 0

    lich_dang_kham = None
    for item in (lich_hom_nay or []):
        if item['trang_thai'] == 'dang_kham':
            lich_dang_kham = LichKhamModel.chi_tiet_lich(item['id'])
            break

    ai_goi_y = None
    patient_health_logs = []
    consultation_messages = []
    if lich_dang_kham:
        symptom_text = lich_dang_kham.get('trieu_chung') or lich_dang_kham.get('ly_do') or ''
        if symptom_text:
            ai_goi_y = DiagnosisService.diagnose({'trieu_chung_text': symptom_text})
        patient_health_logs = HealthTrackingService.list_logs(lich_dang_kham.get('benh_nhan_id'), days=7)
        consultation_messages = ConsultationService.list_messages(lich_dang_kham.get('id'))

    # Thống kê bác sĩ
    ho_so_stats = HoSoModel.thong_ke_bac_si(bac_si_id)

    # Thống kê 7 ngày gần đây cho biểu đồ
    lich_7_ngay = db.query("""
        SELECT DATE(ngay_kham) AS ngay,
               COUNT(*) AS tong,
               SUM(trang_thai='hoan_thanh') AS hoan_thanh,
               SUM(trang_thai='da_huy') AS da_huy
        FROM lich_kham
        WHERE bac_si_id = %s AND ngay_kham >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
        GROUP BY DATE(ngay_kham) ORDER BY ngay
    """, (bac_si_id,))
    # Đánh giá gần đây
    danh_gia_list = db.query("""
        SELECT dg.diem, dg.noi_dung, dg.ngay_tao, nd.ho_ten AS ten_benh_nhan
        FROM danh_gia_bac_si dg
        JOIN benh_nhan bn ON dg.benh_nhan_id = bn.id
        JOIN nguoi_dung nd ON bn.nguoi_dung_id = nd.id
        WHERE dg.bac_si_id = %s ORDER BY dg.ngay_tao DESC LIMIT 5
    """, (bac_si_id,))
    # Thống kê tổng
    tong_hop = db.get_one("""
        SELECT COUNT(*) AS tong_lich,
               SUM(trang_thai='hoan_thanh') AS da_kham,
               SUM(trang_thai='da_huy') AS da_huy,
               COALESCE(AVG(CASE WHEN trang_thai='hoan_thanh' THEN gia_kham END), 0) AS tb_gia
        FROM lich_kham WHERE bac_si_id = %s
    """, (bac_si_id,))
    # Bác sĩ info
    bs_info = db.get_one("""
        SELECT bs.danh_gia, bs.so_danh_gia, ck.ten_chuyen_khoa
        FROM bac_si bs JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
        WHERE bs.id = %s
    """, (bac_si_id,))

    return BaseController.render(
        'bac_si/dashboard.html',
        thong_ke=thong_ke,
        lich_hom_nay=lich_hom_nay,
        doanh_thu=doanh_thu,
        lich_dang_kham=lich_dang_kham,
        ai_goi_y=ai_goi_y,
        patient_health_logs=patient_health_logs,
        patient_health_analysis=HealthTrackingService.analyze(patient_health_logs),
        consultation_messages=consultation_messages,
        ho_so_stats=ho_so_stats,
        lich_7_ngay=lich_7_ngay,
        danh_gia_list=danh_gia_list,
        tong_hop=tong_hop,
        bs_info=bs_info,
    )


# ═══════════════════════════════════════════════════════════════════
# LỊCH KHÁM
# ═══════════════════════════════════════════════════════════════════

@bac_si_bp.route('/lich-kham')
@login_required
@role_required('bac_si')
def lich_kham():
    import calendar
    bac_si_id = session.get('bac_si_id')
    ngay = request.args.get('ngay', date.today().isoformat())

    # Parse tháng/năm
    try:
        selected = date.fromisoformat(ngay)
    except ValueError:
        selected = date.today()

    thang = int(request.args.get('thang', selected.month))
    nam = int(request.args.get('nam', selected.year))

    # Lịch ngày được chọn
    lich_list = LichKhamModel.lich_cua_bac_si(bac_si_id, ngay=ngay)

    # Đếm lịch theo từng ngày trong tháng
    lich_thang = db.query("""
        SELECT DATE(ngay_kham) AS ngay, COUNT(*) AS so_lich,
               SUM(trang_thai='cho_xac_nhan') AS cho_xn,
               SUM(trang_thai='da_xac_nhan') AS da_xn,
               SUM(trang_thai='hoan_thanh') AS hoan_thanh
        FROM lich_kham
        WHERE bac_si_id = %s AND MONTH(ngay_kham) = %s AND YEAR(ngay_kham) = %s
        GROUP BY DATE(ngay_kham)
    """, (bac_si_id, thang, nam))

    # Build dict ngày → số lịch
    lich_dict = {}
    for row in lich_thang:
        ngay_str = row['ngay'].isoformat() if hasattr(row['ngay'], 'isoformat') else str(row['ngay'])
        lich_dict[ngay_str] = {
            'so_lich': row['so_lich'],
            'cho_xn': int(row['cho_xn'] or 0),
            'da_xn': int(row['da_xn'] or 0),
            'hoan_thanh': int(row['hoan_thanh'] or 0),
        }

    # Calendar grid
    cal = calendar.Calendar(firstweekday=0)  # Monday first
    month_days = cal.monthdayscalendar(nam, thang)

    return BaseController.render('bac_si/lich_kham.html',
        lich_list=lich_list,
        ngay=ngay,
        thang=thang,
        nam=nam,
        month_days=month_days,
        lich_dict=lich_dict,
        today=date.today().isoformat(),
    )


@bac_si_bp.route('/xac-nhan/<int:lich_id>', methods=['POST'])
@login_required
@role_required('bac_si')
def xac_nhan_lich(lich_id):
    LichKhamModel.cap_nhat_trang_thai(lich_id, 'da_xac_nhan')

    # Gửi thông báo cho bệnh nhân
    lich = LichKhamModel.chi_tiet_lich(lich_id)
    if lich:
        bn = BenhNhanModel.lay_chi_tiet(lich['benh_nhan_id'])
        if bn:
            ThongBaoModel.gui_thong_bao(
                bn['nguoi_dung_id'] if 'nguoi_dung_id' in bn else None,
                '✅ Lịch khám đã được xác nhận',
                f'Bác sĩ {lich.get("ten_hien_thi_bs", "")} đã xác nhận lịch khám của bạn '
                f'ngày {lich["ngay_kham"]} lúc {lich["gio_kham"]}.',
                loai='lich_kham',
                link=f'/lich-kham/{lich_id}'
            )
            # Gửi Gmail thông báo
            _gui_gmail_thong_bao(
                bn.get('email', ''),
                bn.get('ho_ten', ''),
                f'Xác nhận lịch khám MedPro',
                f"""Xin chào {bn.get('ho_ten', '')},

Lịch khám của bạn đã được xác nhận:
• Bác sĩ: {lich.get('ten_hien_thi_bs', '')}
• Chuyên khoa: {lich.get('ten_chuyen_khoa', '')}
• Ngày khám: {lich.get('ngay_kham', '')}
• Giờ khám: {lich.get('gio_kham', '')}
• Bệnh viện: {lich.get('benh_vien', '')}

Vui lòng đến đúng giờ.

Trân trọng,
Hệ thống MedPro"""
            )

    flash('Đã xác nhận lịch khám.', 'success')
    return redirect(url_for('bac_si.dashboard'))


@bac_si_bp.route('/bat-dau-kham/<int:lich_id>', methods=['POST'])
@login_required
@role_required('bac_si')
def bat_dau_kham(lich_id):
    LichKhamModel.cap_nhat_trang_thai(lich_id, 'dang_kham')
    return redirect(url_for('bac_si.dashboard'))


@bac_si_bp.route('/huy-lich/<int:lich_id>', methods=['POST'])
@login_required
@role_required('bac_si')
def huy_lich(lich_id):
    """Bác sĩ hủy lịch khám."""
    lich = LichKhamModel.chi_tiet_lich(lich_id)
    if lich and lich.get('bac_si_id') == session.get('bac_si_id'):
        if lich['trang_thai'] in ('cho_xac_nhan', 'da_xac_nhan'):
            LichKhamModel.cap_nhat_trang_thai(lich_id, 'da_huy')
            # Thông báo bệnh nhân
            bn = BenhNhanModel.lay_chi_tiet(lich['benh_nhan_id'])
            if bn:
                ThongBaoModel.gui_thong_bao(
                    bn.get('nguoi_dung_id'),
                    '❌ Lịch khám đã bị hủy',
                    f'Bác sĩ {lich.get("ten_hien_thi_bs", "")} đã hủy lịch khám '
                    f'ngày {lich["ngay_kham"]} lúc {lich["gio_kham"]}.',
                    loai='lich_kham',
                )
                # Gửi Gmail
                _gui_gmail_thong_bao(
                    bn.get('email', ''),
                    bn.get('ho_ten', ''),
                    'Thông báo hủy lịch khám MedPro',
                    f"""Xin chào {bn.get('ho_ten', '')},

Lịch khám của bạn đã bị hủy:
• Bác sĩ: {lich.get('ten_hien_thi_bs', '')}
• Ngày khám: {lich.get('ngay_kham', '')}
• Giờ khám: {lich.get('gio_kham', '')}

Vui lòng đặt lại lịch khám mới.

Trân trọng,
Hệ thống MedPro"""
                )
            flash('Đã hủy lịch khám.', 'success')
        else:
            flash('Không thể hủy lịch đang khám hoặc đã hoàn thành.', 'danger')
    else:
        flash('Không tìm thấy lịch khám.', 'danger')
    return redirect(url_for('bac_si.lich_kham'))


# ═══════════════════════════════════════════════════════════════════
# HOÀN THÀNH KHÁM
# ═══════════════════════════════════════════════════════════════════

@bac_si_bp.route('/hoan-thanh/<int:lich_id>', methods=['POST'])
@login_required
@role_required('bac_si')
def hoan_thanh_kham(lich_id):
    bac_si_id = session.get('bac_si_id')
    lich = LichKhamModel.chi_tiet_lich(lich_id)

    if not lich:
        flash('Không tìm thấy lịch khám.', 'danger')
        return redirect(url_for('bac_si.dashboard'))

    chi_dinh = request.form.getlist('chi_dinh')
    ho_so_data = {
        'chan_doan': request.form.get('chan_doan', ''),
        'ghi_chu_lam_sang': request.form.get('ghi_chu_lam_sang', ''),
        'chi_dinh_can_lam_sang': json.dumps(chi_dinh, ensure_ascii=False) if chi_dinh else '[]',
        'huyet_ap': request.form.get('huyet_ap', ''),
        'nhip_tim': request.form.get('nhip_tim'),
        'can_nang': request.form.get('can_nang'),
        'nhiet_do': request.form.get('nhiet_do'),
        'hen_tai_kham': request.form.get('hen_tai_kham') or None,
    }
    ho_so_id = HoSoModel.tao_ho_so(lich_id, lich['benh_nhan_id'], bac_si_id, ho_so_data)

    ten_thuoc_list = request.form.getlist('ten_thuoc[]')
    don_thuoc_chi_tiet = []
    if ten_thuoc_list and any(ten_thuoc_list):
        lieu_dung_list = request.form.getlist('lieu_dung[]')
        so_luong_list = request.form.getlist('so_luong[]')
        don_vi_list = request.form.getlist('don_vi[]')
        for i, ten in enumerate(ten_thuoc_list):
            if ten.strip():
                don_thuoc_chi_tiet.append({
                    'ten_thuoc': ten.strip(),
                    'lieu_dung': lieu_dung_list[i] if i < len(lieu_dung_list) else '',
                    'so_luong': int(so_luong_list[i]) if i < len(so_luong_list) and so_luong_list[i] else 1,
                    'don_vi': don_vi_list[i] if i < len(don_vi_list) else 'vien',
                })
        if don_thuoc_chi_tiet:
            DonThuocModel.tao_don_thuoc(
                ho_so_id,
                lich['benh_nhan_id'],
                bac_si_id,
                request.form.get('ghi_chu_thuoc', ''),
                don_thuoc_chi_tiet,
            )

    LichKhamModel.cap_nhat_trang_thai(lich_id, 'hoan_thanh')

    # Gửi thông báo + Gmail cho bệnh nhân
    bn = BenhNhanModel.lay_chi_tiet(lich['benh_nhan_id'])
    if bn:
        ThongBaoModel.gui_thong_bao(
            bn.get('nguoi_dung_id'),
            '🏥 Khám bệnh hoàn thành',
            f'Bác sĩ {lich.get("ten_hien_thi_bs", "")} đã hoàn thành khám. '
            f'Chẩn đoán: {ho_so_data.get("chan_doan", "")}',
            loai='ho_so',
            link=f'/ho-so/chi-tiet/{ho_so_id}'
        )

        # Build nội dung email đơn thuốc
        thuoc_text = ''
        if don_thuoc_chi_tiet:
            thuoc_text = '\n📋 ĐƠN THUỐC:\n'
            for i, t in enumerate(don_thuoc_chi_tiet, 1):
                thuoc_text += f"  {i}. {t['ten_thuoc']} - {t.get('lieu_dung', '')} - SL: {t.get('so_luong', 1)} {t.get('don_vi', 'viên')}\n"

        hen_text = ''
        if ho_so_data.get('hen_tai_kham'):
            hen_text = f'\n📅 HẸN TÁI KHÁM: {ho_so_data["hen_tai_kham"]}\n'

        _gui_gmail_thong_bao(
            bn.get('email', ''),
            bn.get('ho_ten', ''),
            f'Kết quả khám bệnh - MedPro',
            f"""Xin chào {bn.get('ho_ten', '')},

Kết quả khám bệnh của bạn:
• Bác sĩ: {lich.get('ten_hien_thi_bs', '')}
• Chuyên khoa: {lich.get('ten_chuyen_khoa', '')}
• Ngày khám: {lich.get('ngay_kham', '')}

🔍 CHẨN ĐOÁN: {ho_so_data.get('chan_doan', 'Chưa ghi')}

📝 GHI CHÚ LÂM SÀNG:
{ho_so_data.get('ghi_chu_lam_sang', 'Không có')}
{thuoc_text}{hen_text}
Vui lòng truy cập hệ thống MedPro để xem chi tiết.

Trân trọng,
Hệ thống MedPro"""
        )

    flash('Hoàn thành khám bệnh.', 'success')
    return redirect(url_for('bac_si.dashboard'))


# ═══════════════════════════════════════════════════════════════════
# THÔNG TIN CÁ NHÂN BÁC SĨ (chỉ xem, KHÔNG sửa)
# ═══════════════════════════════════════════════════════════════════

@bac_si_bp.route('/thong-tin')
@login_required
@role_required('bac_si')
def thong_tin_ca_nhan():
    """Xem thông tin cá nhân bác sĩ (read-only)."""
    bac_si_id = session.get('bac_si_id')
    bs = db.get_one("""
        SELECT bs.*, nd.ho_ten, nd.email, nd.so_dien_thoai, nd.avatar,
               ck.ten_chuyen_khoa
        FROM bac_si bs
        JOIN nguoi_dung nd ON bs.nguoi_dung_id = nd.id
        JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
        WHERE bs.id = %s
    """, (bac_si_id,))
    return BaseController.render(
        'bac_si/thong_tin.html',
        bac_si=bs,
    )


# ═══════════════════════════════════════════════════════════════════
# BỆNH NHÂN CỦA TÔI
# ═══════════════════════════════════════════════════════════════════

@bac_si_bp.route('/benh-nhan')
@login_required
@role_required('bac_si')
def benh_nhan_cua_toi():
    """Danh sách bệnh nhân của bác sĩ"""
    bac_si_id = session.get('bac_si_id')
    search = request.args.get('q', '').strip()
    benh_nhan_list = HoSoModel.benh_nhan_cua_bac_si(bac_si_id, search)
    return BaseController.render(
        'bac_si/benh_nhan.html',
        benh_nhan_list=benh_nhan_list,
        search=search,
    )


@bac_si_bp.route('/benh-nhan/<int:benh_nhan_id>')
@login_required
@role_required('bac_si')
def chi_tiet_benh_nhan(benh_nhan_id):
    """Xem chi tiết bệnh nhân mà bác sĩ đã khám"""
    bac_si_id = session.get('bac_si_id')

    # Kiểm tra bác sĩ có quyền xem bệnh nhân này
    check = db.get_one("""
        SELECT COUNT(*) AS cnt FROM lich_kham
        WHERE bac_si_id = %s AND benh_nhan_id = %s
        AND trang_thai IN ('da_xac_nhan','dang_kham','hoan_thanh')
    """, (bac_si_id, benh_nhan_id))
    if not check or check['cnt'] == 0:
        flash('Bạn chưa có lịch khám với bệnh nhân này.', 'danger')
        return redirect(url_for('bac_si.benh_nhan_cua_toi'))

    benh_nhan = BenhNhanModel.lay_chi_tiet(benh_nhan_id)
    if not benh_nhan:
        flash('Không tìm thấy bệnh nhân.', 'warning')
        return redirect(url_for('bac_si.benh_nhan_cua_toi'))

    # Hồ sơ bệnh án của bệnh nhân này (tất cả bác sĩ đã khám)
    ho_so_list = HoSoModel.timeline_benh_nhan(benh_nhan_id)
    # Đơn thuốc
    don_thuoc_list = DonThuocModel.lay_tat_ca_theo_benh_nhan(benh_nhan_id)
    for don in don_thuoc_list:
        don['chi_tiet'] = DonThuocModel.lay_chi_tiet_cua_don(don['id'])

    return BaseController.render(
        'bac_si/chi_tiet_benh_nhan.html',
        benh_nhan=benh_nhan,
        ho_so_list=ho_so_list,
        don_thuoc_list=don_thuoc_list,
        bac_si_id=bac_si_id,
    )


# ═══════════════════════════════════════════════════════════════════
# CƠ SỞ DỮ LIỆU THUỐC (tra cứu cho kê đơn)
# ═══════════════════════════════════════════════════════════════════

@bac_si_bp.route('/co-so-thuoc')
@login_required
@role_required('bac_si')
def co_so_thuoc():
    """Trang tra cứu cơ sở dữ liệu thuốc"""
    keyword = request.args.get('q', '').strip()
    chan_doan = request.args.get('chan_doan', '').strip()
    thuoc_list = []
    mode = 'search'

    if chan_doan:
        thuoc_list = DonThuocModel.search_thuoc_theo_benh(chan_doan, limit=50)
        mode = 'by_disease'
    elif keyword and len(keyword) >= 2:
        thuoc_list = DonThuocModel.search_danh_muc(keyword, limit=50)

    return BaseController.render(
        'bac_si/co_so_thuoc.html',
        thuoc_list=thuoc_list,
        keyword=keyword,
        chan_doan=chan_doan,
        mode=mode,
    )


# ═══════════════════════════════════════════════════════════════════
# API
# ═══════════════════════════════════════════════════════════════════

@bac_si_bp.route('/api/ai-goi-y', methods=['POST'])
@login_required
@role_required('bac_si')
def api_ai_goi_y():
    payload = request.get_json(silent=True) or {}
    result = DiagnosisService.diagnose(payload)
    return BaseController.json_response(result, message='Da tao goi y AI.')


@bac_si_bp.route('/api/tu-van', methods=['POST'])
@login_required
@role_required('bac_si')
def api_tu_van():
    payload = request.get_json(silent=True) or {}
    lich_id = payload.get('lich_kham_id')
    lich = LichKhamModel.chi_tiet_lich(lich_id) if lich_id else None
    if not lich:
        return BaseController.json_error('Khong tim thay lich kham.', status=404)
    if lich.get('bac_si_id') != session.get('bac_si_id'):
        return BaseController.json_error('Khong co quyen tu van lich nay.', status=403)
    try:
        message = ConsultationService.add_message(
            lich.get('id'),
            lich.get('benh_nhan_id'),
            session.get('bac_si_id'),
            'bac_si',
            payload.get('noi_dung', ''),
        )
        return BaseController.json_response(message, message='Da luu tin nhan tu van.')
    except ValueError as exc:
        return BaseController.json_error(str(exc), status=422)


@bac_si_bp.route('/api/search-thuoc')
@login_required
@role_required('bac_si')
def api_search_thuoc():
    """API tìm thuốc từ danh mục 2000 loại cho autocomplete."""
    keyword = request.args.get('q', '').strip()
    results = DonThuocModel.search_danh_muc(keyword, limit=15)
    return BaseController.json_response({'items': results})


@bac_si_bp.route('/api/thuoc-theo-benh')
@login_required
@role_required('bac_si')
def api_thuoc_theo_benh():
    """API gợi ý thuốc theo chẩn đoán/bệnh."""
    chan_doan = request.args.get('chan_doan', '').strip()
    results = DonThuocModel.search_thuoc_theo_benh(chan_doan, limit=20)
    return BaseController.json_response({'items': results})


@bac_si_bp.route('/api/ho-so/<int:ho_so_id>')
@login_required
@role_required('bac_si')
def api_chi_tiet_ho_so(ho_so_id):
    """API lấy chi tiết 1 hồ sơ bệnh án."""
    hs = HoSoModel.lay_chi_tiet_day_du(ho_so_id)
    if not hs:
        return BaseController.json_error('Không tìm thấy hồ sơ.', status=404)
    don_thuoc = DonThuocModel.lay_theo_ho_so(ho_so_id)
    return BaseController.json_response({'ho_so': hs, 'don_thuoc': don_thuoc})


@bac_si_bp.route('/api/ho-so/tao', methods=['POST'])
@login_required
@role_required('bac_si')
def api_tao_ho_so():
    """API tạo hồ sơ bệnh án mới (không qua lịch khám)."""
    bac_si_id = session.get('bac_si_id')
    payload = request.get_json(silent=True) or {}
    benh_nhan_id = payload.get('benh_nhan_id')
    if not benh_nhan_id:
        return BaseController.json_error('Thiếu benh_nhan_id.', status=400)

    # Tìm lich_kham gần nhất
    lich = db.get_one("""
        SELECT id FROM lich_kham
        WHERE bac_si_id = %s AND benh_nhan_id = %s
        ORDER BY ngay_kham DESC LIMIT 1
    """, (bac_si_id, benh_nhan_id))
    lich_id = lich['id'] if lich else None

    if not lich_id:
        return BaseController.json_error('Bệnh nhân chưa có lịch khám nào với bạn.', status=400)

    ho_so_data = {
        'chan_doan': payload.get('chan_doan', ''),
        'ghi_chu_lam_sang': payload.get('ghi_chu_lam_sang', ''),
        'huyet_ap': payload.get('huyet_ap', ''),
        'nhip_tim': payload.get('nhip_tim'),
        'can_nang': payload.get('can_nang'),
        'nhiet_do': payload.get('nhiet_do'),
        'hen_tai_kham': payload.get('hen_tai_kham') or None,
    }
    ho_so_id = HoSoModel.tao_ho_so(lich_id, benh_nhan_id, bac_si_id, ho_so_data)
    return BaseController.json_response({'ho_so_id': ho_so_id}, message='Đã tạo hồ sơ bệnh án.')


@bac_si_bp.route('/api/ho-so/sua/<int:ho_so_id>', methods=['POST'])
@login_required
@role_required('bac_si')
def api_sua_ho_so(ho_so_id):
    """API sửa hồ sơ bệnh án."""
    bac_si_id = session.get('bac_si_id')
    ho_so = HoSoModel.get_by_id(ho_so_id)
    if not ho_so or ho_so['bac_si_id'] != bac_si_id:
        return BaseController.json_error('Không có quyền sửa hồ sơ này.', status=403)
    payload = request.get_json(silent=True) or {}
    data = {}
    for field in ('chan_doan', 'ghi_chu_lam_sang', 'huyet_ap', 'hen_tai_kham'):
        if field in payload:
            data[field] = payload[field]
    for field in ('nhip_tim', 'can_nang', 'nhiet_do'):
        if field in payload and payload[field]:
            try:
                data[field] = float(payload[field])
            except (ValueError, TypeError):
                pass
    HoSoModel.cap_nhat_ho_so(ho_so_id, data)
    return BaseController.json_response(message='Đã cập nhật hồ sơ.')


@bac_si_bp.route('/api/ho-so/xoa/<int:ho_so_id>', methods=['POST'])
@login_required
@role_required('bac_si')
def api_xoa_ho_so(ho_so_id):
    """API xóa hồ sơ bệnh án."""
    bac_si_id = session.get('bac_si_id')
    ho_so = HoSoModel.get_by_id(ho_so_id)
    if not ho_so or ho_so['bac_si_id'] != bac_si_id:
        return BaseController.json_error('Không có quyền xóa.', status=403)
    HoSoModel.xoa_ho_so(ho_so_id)
    return BaseController.json_response(message='Đã xóa hồ sơ bệnh án.')


@bac_si_bp.route('/api/don-thuoc/tao', methods=['POST'])
@login_required
@role_required('bac_si')
def api_tao_don_thuoc():
    """API tạo đơn thuốc cho hồ sơ."""
    bac_si_id = session.get('bac_si_id')
    payload = request.get_json(silent=True) or {}
    ho_so_id = payload.get('ho_so_id')
    benh_nhan_id = payload.get('benh_nhan_id')
    ghi_chu = payload.get('ghi_chu', '')
    chi_tiet = payload.get('chi_tiet', [])

    if not ho_so_id or not benh_nhan_id:
        return BaseController.json_error('Thiếu ho_so_id hoặc benh_nhan_id.', status=400)
    if not chi_tiet:
        return BaseController.json_error('Đơn thuốc trống.', status=400)

    ho_so = HoSoModel.get_by_id(ho_so_id)
    if not ho_so or ho_so['bac_si_id'] != bac_si_id:
        return BaseController.json_error('Không có quyền kê đơn cho hồ sơ này.', status=403)

    don_id = DonThuocModel.tao_don_thuoc(ho_so_id, benh_nhan_id, bac_si_id, ghi_chu, chi_tiet)
    return BaseController.json_response({'don_thuoc_id': don_id}, message='Đã tạo đơn thuốc.')


@bac_si_bp.route('/api/don-thuoc/sua/<int:don_id>', methods=['POST'])
@login_required
@role_required('bac_si')
def api_sua_don_thuoc(don_id):
    """API sửa đơn thuốc."""
    bac_si_id = session.get('bac_si_id')
    don = DonThuocModel.get_by_id(don_id)
    if not don or don['bac_si_id'] != bac_si_id:
        return BaseController.json_error('Không có quyền sửa.', status=403)
    payload = request.get_json(silent=True) or {}
    DonThuocModel.cap_nhat_don_thuoc(don_id, payload.get('ghi_chu', ''), payload.get('chi_tiet', []))
    return BaseController.json_response(message='Đã cập nhật đơn thuốc.')


@bac_si_bp.route('/api/don-thuoc/xoa/<int:don_id>', methods=['POST'])
@login_required
@role_required('bac_si')
def api_xoa_don_thuoc(don_id):
    """API xóa đơn thuốc."""
    bac_si_id = session.get('bac_si_id')
    don = DonThuocModel.get_by_id(don_id)
    if not don or don['bac_si_id'] != bac_si_id:
        return BaseController.json_error('Không có quyền xóa.', status=403)
    DonThuocModel.xoa_don_thuoc(don_id)
    return BaseController.json_response(message='Đã xóa đơn thuốc.')


# ═══════════════════════════════════════════════════════════════════
# API: CẬP NHẬT THÔNG TIN, AVATAR, ĐỔI MẬT KHẨU
# ═══════════════════════════════════════════════════════════════════

@bac_si_bp.route('/api/cap-nhat-thong-tin', methods=['POST'])
@login_required
@role_required('bac_si')
def api_cap_nhat_thong_tin():
    """API cập nhật thông tin cá nhân bác sĩ."""
    bac_si_id = session.get('bac_si_id')
    nguoi_dung_id = session.get('user_id')
    payload = request.get_json(silent=True) or {}

    # Cập nhật bảng nguoi_dung
    nd_data = {}
    if 'ho_ten' in payload and payload['ho_ten'].strip():
        nd_data['ho_ten'] = payload['ho_ten'].strip()
    if 'so_dien_thoai' in payload:
        nd_data['so_dien_thoai'] = payload['so_dien_thoai'].strip()
    if 'email' in payload and payload['email'].strip():
        new_email = payload['email'].strip().lower()
        # Kiểm tra email trùng (trừ chính mình)
        existing = db.get_one(
            "SELECT id FROM nguoi_dung WHERE email = %s AND id != %s",
            (new_email, nguoi_dung_id)
        )
        if existing:
            return BaseController.json_error('Email đã được sử dụng bởi tài khoản khác.', status=400)
        nd_data['email'] = new_email
    if nd_data:
        NguoiDungModel.update(nguoi_dung_id, nd_data)

    # Cập nhật bảng bac_si
    bs_data = {}
    for field in ('hoc_vi', 'benh_vien', 'dia_chi_phong_kham', 'mo_ta'):
        if field in payload:
            bs_data[field] = payload[field]
    for field in ('gia_kham', 'kinh_nghiem'):
        if field in payload:
            try:
                bs_data[field] = float(payload[field])
            except (ValueError, TypeError):
                pass
    if bs_data:
        BacSiModel.update(bac_si_id, bs_data)

    return BaseController.json_response(message='Đã cập nhật thông tin.')


@bac_si_bp.route('/api/reset-thong-tin', methods=['POST'])
@login_required
@role_required('bac_si')
def api_reset_thong_tin():
    """Reset thông tin bác sĩ về mặc định."""
    bac_si_id = session.get('bac_si_id')
    BacSiModel.update(bac_si_id, {
        'hoc_vi': 'BS',
        'benh_vien': '',
        'dia_chi_phong_kham': '',
        'mo_ta': '',
        'gia_kham': 150000,
        'kinh_nghiem': 0,
    })
    return BaseController.json_response(message='Đã reset thông tin.')


@bac_si_bp.route('/api/avatar', methods=['POST'])
@login_required
@role_required('bac_si')
def api_upload_avatar():
    """Upload ảnh đại diện bác sĩ."""
    import os
    from werkzeug.utils import secure_filename
    from flask import current_app

    file = request.files.get('avatar')
    if not file or file.filename == '':
        return BaseController.json_error('Chưa chọn ảnh.', status=400)

    allowed = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        return BaseController.json_error('Chỉ chấp nhận ảnh PNG, JPG, WEBP.', status=400)

    nguoi_dung_id = session.get('user_id')
    filename = f"doctor_{nguoi_dung_id}.{ext}"
    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'avatars')
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))

    NguoiDungModel.update(nguoi_dung_id, {'avatar': filename})
    return BaseController.json_response(message='Đã cập nhật ảnh đại diện.')


@bac_si_bp.route('/api/doi-mat-khau', methods=['POST'])
@login_required
@role_required('bac_si')
def api_doi_mat_khau():
    """API đổi mật khẩu bác sĩ."""
    from werkzeug.security import check_password_hash, generate_password_hash

    nguoi_dung_id = session.get('user_id')
    payload = request.get_json(silent=True) or {}
    mat_khau_cu = payload.get('mat_khau_cu', '')
    mat_khau_moi = payload.get('mat_khau_moi', '')

    if not mat_khau_cu or not mat_khau_moi:
        return BaseController.json_error('Vui lòng nhập đủ thông tin.', status=400)
    if len(mat_khau_moi) < 6:
        return BaseController.json_error('Mật khẩu mới tối thiểu 6 ký tự.', status=400)

    user = NguoiDungModel.get_by_id(nguoi_dung_id)
    if not user or not check_password_hash(user['mat_khau'], mat_khau_cu):
        return BaseController.json_error('Mật khẩu hiện tại không đúng.', status=400)

    NguoiDungModel.update(nguoi_dung_id, {
        'mat_khau': generate_password_hash(mat_khau_moi)
    })
    return BaseController.json_response(message='Đã đổi mật khẩu thành công.')





# ═══════════════════════════════════════════════════════════════════
# HELPER: GỬI EMAIL THÔNG BÁO (dùng cho thông báo hệ thống)
# ═══════════════════════════════════════════════════════════════════

def _gui_gmail_thong_bao(email: str, ho_ten: str, tieu_de: str, noi_dung: str) -> bool:
    """Gửi email qua SMTP (Gmail). Nếu chưa cấu hình SMTP_USER thì log ra console."""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from config import Config

        if not email:
            return False

        if not Config.SMTP_USER:
            logger.info("[EMAIL LOG] To: %s | Subject: %s | Body: %s", email, tieu_de, noi_dung[:200])
            return True

        msg = MIMEMultipart('alternative')
        msg['Subject'] = tieu_de
        msg['From'] = f"MedPro <{Config.SMTP_USER}>"
        msg['To'] = email

        # HTML email
        html_body = f"""
        <div style="font-family:'Inter',Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;">
            <div style="background:linear-gradient(135deg,#059669,#0891b2);padding:30px;border-radius:16px 16px 0 0;">
                <h1 style="color:#fff;margin:0;font-size:24px;">🏥 MedPro</h1>
                <p style="color:rgba(255,255,255,0.8);margin:8px 0 0;font-size:14px;">Hệ thống Chăm Sóc Sức Khỏe</p>
            </div>
            <div style="padding:30px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:0 0 16px 16px;">
                <h2 style="color:#0f172a;margin:0 0 16px;font-size:18px;">{tieu_de}</h2>
                <div style="background:#fff;padding:20px;border-radius:12px;border:1px solid #e2e8f0;
                            white-space:pre-line;color:#334155;font-size:14px;line-height:1.7;">
{noi_dung}
                </div>
                <p style="color:#94a3b8;font-size:12px;margin-top:20px;text-align:center;">
                    Email tự động từ hệ thống MedPro. Vui lòng không phản hồi.
                </p>
            </div>
        </div>
        """
        msg.attach(MIMEText(noi_dung, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.SMTP_USER, Config.SMTP_PASS)
            server.send_message(msg)

        logger.info("[EMAIL SENT] To: %s | Subject: %s", email, tieu_de)
        return True
    except Exception as e:
        logger.error("[EMAIL ERROR] %s", e)
        return False
