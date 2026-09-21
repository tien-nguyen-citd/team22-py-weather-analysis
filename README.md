# Phân tích dữ liệu thời tiết

Ứng dụng gồm frontend React, backend FastAPI và dịch vụ NLU đọc câu hỏi tiếng Việt.

## Yêu cầu

- Python 3.14
- Node.js
- Windows PowerShell
- SQL Server Express LocalDB
- ODBC Driver 17 hoặc 18 for SQL Server

## Setup lần đầu

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python -m weather_analysis.seed
python -m weather_analysis.preload_climate
```

Lệnh seed tự chạy migration và nạp tài khoản, địa điểm mẫu. Lệnh
`preload_climate` nạp trước lịch sử khí hậu cho các điểm dùng trong tính năng
xếp hạng điểm đến; lần đầu có thể mất vài phút, gặp lỗi thì chạy lại lệnh.

### Frontend

```powershell
cd frontend
npm install
```

### NLU service

Tab **Tư vấn** cần NLU service tại port `8002`. Setup và chạy service theo
[hướng dẫn riêng của NLU service](nlu-service/README.md).

## Chạy môi trường dev

Mở hai terminal từ thư mục gốc của dự án.

Terminal 1 — backend tại `http://localhost:8000`:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn weather_analysis.api.app:app --reload
```

Terminal 2 — frontend tại `http://localhost:5173`:

```powershell
cd frontend
npm run dev
```

Khi làm việc với tab **Tư vấn**, mở thêm terminal và chạy NLU service theo
[`nlu-service/README.md`](nlu-service/README.md#chạy-service).

Trang quản trị: `http://localhost:5173/admin/dang-nhap`

- Tên đăng nhập: `admin`
- Mật khẩu: `adminpw`

Backend cần Internet để lấy dữ liệu từ Open-Meteo. Lần đầu chạy NLU service
cũng cần Internet để tải model.

## Kiểm tra

Backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pyright
ruff check .
pytest -q
```

Frontend:

```powershell
cd frontend
npm run lint
npm run build
npm test
```

E2E:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest tests/e2e
```

Không cần bật sẵn ứng dụng khi chạy E2E. Xem thêm lệnh kiểm tra NLU trong
[`nlu-service/README.md`](nlu-service/README.md#chạy-kiểm-tra).

## Biến môi trường thường dùng

- `WEATHER_DB_URL`: URL kết nối SQLAlchemy; mặc định dùng SQL Server LocalDB.
- `WEATHER_SESSION_SECRET`: khóa ký session cookie; bắt buộc đổi khi triển khai thật.
- `WEATHER_API_URL`: backend cho Vite proxy; mặc định `http://localhost:8000`.
- `WEATHER_NLU_URL`: NLU service cho Vite proxy; mặc định `http://localhost:8002`.
