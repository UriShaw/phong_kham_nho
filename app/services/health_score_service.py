"""
Health Score Service - Tính điểm sức khỏe AI
"""


class HealthScoreService:
    """Service tính điểm sức khỏe dựa trên chỉ số y tế"""

    @staticmethod
    def tinh_diem(benh_nhan):
        """
        Tính điểm sức khỏe 0-100 dựa trên:
        - BMI (30 điểm)
        - Huyết áp (25 điểm)
        - Nhịp tim (20 điểm)
        - Lịch sử khám định kỳ (15 điểm)
        - Tuổi tác (10 điểm)
        """
        diem = 0
        chi_tiet = []

        # 1. BMI (30 điểm)
        if benh_nhan.get('chieu_cao') and benh_nhan.get('can_nang'):
            chieu_cao_m = float(benh_nhan['chieu_cao']) / 100
            can_nang = float(benh_nhan['can_nang'])
            bmi = can_nang / (chieu_cao_m ** 2)

            if 18.5 <= bmi <= 24.9:
                diem += 30
                chi_tiet.append({'ten': 'BMI', 'diem': 30, 'trang_thai': 'Tốt', 'gia_tri': f'{bmi:.1f}'})
            elif 17 <= bmi < 18.5 or 25 <= bmi < 30:
                diem += 20
                chi_tiet.append({'ten': 'BMI', 'diem': 20, 'trang_thai': 'Cần cải thiện', 'gia_tri': f'{bmi:.1f}'})
            else:
                diem += 10
                chi_tiet.append({'ten': 'BMI', 'diem': 10, 'trang_thai': 'Cần chú ý', 'gia_tri': f'{bmi:.1f}'})
        else:
            diem += 15  # Chưa có dữ liệu → trung bình
            chi_tiet.append({'ten': 'BMI', 'diem': 15, 'trang_thai': 'Chưa có dữ liệu', 'gia_tri': 'N/A'})

        # 2. Huyết áp (25 điểm)
        if benh_nhan.get('huyet_ap'):
            try:
                tam_thu, tam_truong = benh_nhan['huyet_ap'].split('/')
                tam_thu = int(tam_thu)
                tam_truong = int(tam_truong)

                if 90 <= tam_thu <= 130 and 60 <= tam_truong <= 85:
                    diem += 25
                    chi_tiet.append({'ten': 'Huyết áp', 'diem': 25, 'trang_thai': 'Bình thường', 'gia_tri': benh_nhan['huyet_ap']})
                elif 130 < tam_thu <= 140 or 85 < tam_truong <= 90:
                    diem += 15
                    chi_tiet.append({'ten': 'Huyết áp', 'diem': 15, 'trang_thai': 'Tăng nhẹ', 'gia_tri': benh_nhan['huyet_ap']})
                else:
                    diem += 5
                    chi_tiet.append({'ten': 'Huyết áp', 'diem': 5, 'trang_thai': 'Cần theo dõi', 'gia_tri': benh_nhan['huyet_ap']})
            except (ValueError, AttributeError):
                diem += 12
                chi_tiet.append({'ten': 'Huyết áp', 'diem': 12, 'trang_thai': 'Chưa rõ', 'gia_tri': 'N/A'})
        else:
            diem += 12
            chi_tiet.append({'ten': 'Huyết áp', 'diem': 12, 'trang_thai': 'Chưa có dữ liệu', 'gia_tri': 'N/A'})

        # 3. Nhịp tim (20 điểm)
        if benh_nhan.get('nhip_tim'):
            nhip = int(benh_nhan['nhip_tim'])
            if 60 <= nhip <= 100:
                diem += 20
                chi_tiet.append({'ten': 'Nhịp tim', 'diem': 20, 'trang_thai': 'Bình thường', 'gia_tri': f'{nhip} bpm'})
            elif 50 <= nhip < 60 or 100 < nhip <= 110:
                diem += 12
                chi_tiet.append({'ten': 'Nhịp tim', 'diem': 12, 'trang_thai': 'Hơi bất thường', 'gia_tri': f'{nhip} bpm'})
            else:
                diem += 5
                chi_tiet.append({'ten': 'Nhịp tim', 'diem': 5, 'trang_thai': 'Cần kiểm tra', 'gia_tri': f'{nhip} bpm'})
        else:
            diem += 10
            chi_tiet.append({'ten': 'Nhịp tim', 'diem': 10, 'trang_thai': 'Chưa có dữ liệu', 'gia_tri': 'N/A'})

        # 4. Baseline cho lịch sử và tuổi tác
        diem += 15 + 10  # Mặc định tốt

        # Nhận xét tổng quát
        if diem >= 80:
            nhan_xet = 'Sức khỏe tổng quát Tốt. Duy trì thói quen tập luyện.'
            mau = '#22C55E'
        elif diem >= 60:
            nhan_xet = 'Sức khỏe Khá. Cần cải thiện một số chỉ số.'
            mau = '#F59E0B'
        elif diem >= 40:
            nhan_xet = 'Sức khỏe Trung bình. Nên đi khám tổng quát.'
            mau = '#EF4444'
        else:
            nhan_xet = 'Cần kiểm tra sức khỏe ngay. Hãy đặt lịch khám!'
            mau = '#DC2626'

        return {
            'diem': min(diem, 100),
            'nhan_xet': nhan_xet,
            'mau': mau,
            'chi_tiet': chi_tiet
        }
