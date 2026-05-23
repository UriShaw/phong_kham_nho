# 🏥 MedPro - Phần Mềm Quản Lý Dịch Vụ Chăm Sóc Sức Khỏe

Hệ thống đặt lịch khám bệnh trực tuyến tương tự MedPro / BookingCare.

## ✨ Tính năng chính

### 👤 Bệnh nhân
- Đăng ký / Đăng nhập
- Tìm bác sĩ theo chuyên khoa, bệnh viện, giá khám
- Đặt lịch khám chỉ trong 3 bước
- Thanh toán QR (MB Bank)
- Xem hồ sơ sức khỏe (timeline)
- Điểm sức khỏe AI (Health Score)
- Quản lý gia đình
- Nhận thông báo

### 🩺 Bác sĩ
- Dashboard thống kê ca khám
- Xem / xác nhận lịch khám
- Khám bệnh trực tuyến (ghi chú, chẩn đoán)
- Tạo đơn thuốc điện tử

### 👨‍💼 Admin
- Dashboard tổng quan hệ thống
- Quản lý bác sĩ (duyệt hồ sơ)
- Quản lý bệnh nhân
- Quản lý lịch khám
- Thống kê biểu đồ theo chuyên khoa

### 🤖 AI Chatbot
- Tư vấn triệu chứng → gợi ý chuyên khoa
- Gợi ý bác sĩ phù hợp
- Trả lời FAQ (giờ khám, chi phí, quy trình)

### 💳 Thanh toán QR
- Tạo mã QR tự động qua VietQR API
- Ngân hàng: MB Bank
- STK: 0965117393 - NGUYEN QUOC ANH

---

## 🛠️ Công nghệ

| Thành phần | Công nghệ |
|-----------|-----------|
| Frontend | HTML, CSS (Glassmorphism), JavaScript |
| Backend | Python Flask |
| Database | MySQL (XAMPP) |
| Icons | Font Awesome 6 |
| Fonts | Google Fonts (Inter) |
| QR | VietQR API |

---

## 📦 Cài đặt

### Yêu cầu
- Python 3.8+
- XAMPP (MySQL)
- pip

### Bước 1: Cài đặt dependencies
```bash
cd d:\btlpython
pip install -r requirements.txt
```

### Bước 2: Khởi động MySQL (XAMPP)
- Mở XAMPP Control Panel
- Bấm **Start** MySQL
- Đảm bảo MySQL chạy trên port **3306**

### Bước 3: Khởi tạo Database
```bash
python init_db.py
```

### Bước 4: Chạy ứng dụng
```bash
python run.py
```

### Bước 5: Truy cập
Mở trình duyệt: **http://localhost:5000**

---

## 🔐 Tài khoản mẫu

| Vai trò | Email | Mật khẩu |
|---------|-------|-----------|
| Admin | admin@medpro.vn | admin123 |
| Bác sĩ | bs.nguyen@medpro.vn | bacsi123 |
| Bệnh nhân | bn.nguyen@medpro.vn | benhnhan123 |

---

## 📁 Cấu trúc thư mục

```
btlpython/
├── run.py                 # Entry point
├── config.py              # Cấu hình
├── init_db.py             # Khởi tạo DB
├── .env                   # Biến môi trường
├── requirements.txt       # Dependencies
│
├── core/                  # Lõi MVC
│   ├── database.py        # Kết nối MySQL
│   ├── model.py           # Base Model CRUD
│   ├── controller.py      # Base Controller
│   ├── middleware.py       # Auth, CSRF
│   └── router.py          # Đăng ký routes
│
├── app/
│   ├── controllers/       # 8 controllers
│   ├── models/            # 8 models
│   ├── services/          # 6 services
│   └── views/             # 20+ templates
│
├── public/static/
│   ├── css/style.css      # Glassmorphism CSS
│   └── js/                # JavaScript
│
└── database/
    └── schema.sql         # SQL schema + data
```

---

## 🧠 Tiện ích sức khỏe nâng cấp

### Module

- **BMI 3D**: `/tien-ich/bmi`, API `POST /tien-ich/api/bmi`
- **Theo dõi sức khỏe**: `/tien-ich/suc-khoe`, API `GET|POST /tien-ich/api/suc-khoe`
- **Nhắc uống thuốc Gmail**: `/tien-ich/nhac-thuoc`, API `GET|POST|DELETE /tien-ich/api/nhac-thuoc`
- **AI triệu chứng**: `/tien-ich/chan-doan`, API `POST /tien-ich/api/chan-doan`
- **Admin kho dữ liệu**: `/admin/kho-du-lieu`

### Cấu trúc mới

```
app/
├── data/
│   ├── health_knowledge.json          # Thực phẩm, calories, bài tập, kế hoạch tuần
│   └── symptom_disease_dataset.json   # Triệu chứng, bệnh, chuyên khoa, red flags
├── services/
│   ├── bmi_service.py
│   ├── health_tracking_service.py
│   ├── medication_reminder_service.py
│   ├── diagnosis_service.py
│   ├── consultation_service.py
│   └── utility_schema_service.py
└── controllers/
    └── tien_ich_controller.py         # REST API + HTML routes
```

### Gmail SMTP

Thêm vào `.env` nếu muốn gửi email thật:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_gmail@gmail.com
SMTP_PASS=your_gmail_app_password
```

Nếu chưa cấu hình SMTP, scheduler vẫn chạy và ghi log email để demo.

### Database bổ sung

`database/schema.sql` đã thêm:

- `suc_khoe_log`
- `nhac_thuoc`
- `ai_chan_doan_log`
- `tu_van_tin_nhan`

Các API mới cũng tự gọi `UtilitySchemaService.ensure()` để tạo bảng còn thiếu trên database cũ.

---

## 🎨 Giao diện

- **Phong cách**: Glassmorphism (kính mờ)
- **Màu chủ đạo**: Xanh lá (#22C55E) + Trắng
- **Font**: Inter (Google Fonts)
- **Hiệu ứng**: Hover, Fade, Slide, Loading Skeleton
- **Responsive**: Desktop + Mobile

---

## 📌 Ghi chú

- Toàn bộ giao diện bằng **tiếng Việt**
- Comment code bằng **tiếng Việt**
- Thanh toán QR sử dụng VietQR API (miễn phí)
- Chatbot hoạt động rule-based (không cần API key)
- Dữ liệu mẫu được tạo sẵn khi chạy `init_db.py`

---

**© 2024 MedPro Clone** - Đồ án Phần Mềm Quản Lý Dịch Vụ Chăm Sóc Sức Khỏe
