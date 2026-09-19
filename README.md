# Phân tích dữ liệu thời tiết

Ứng dụng minh họa cách tổ chức frontend React và backend Python cho một sản phẩm phân tích dữ liệu thời tiết thực tế.

## Yêu cầu

- Python 3.14
- Node.js
- Windows PowerShell
- SQL Server Express LocalDB
- ODBC Driver 17 hoặc 18 for SQL Server

## Cài đặt

Cài đặt backend và khởi tạo dữ liệu mẫu:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python -m weather_analysis.seed
```

Lệnh seed tự chạy các migration còn thiếu rồi nạp tài khoản và 91 địa điểm mẫu.
Các lần chạy sau không ghi đè danh sách địa điểm đã được quản trị viên nhập.

Nếu database LocalDB được tạo từ phiên bản cũ và đã có bảng `users` nhưng chưa
có bảng `alembic_version`, đánh dấu migration baseline trước khi nâng cấp:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic stamp 0001
alembic upgrade head
alembic current
```

Với database mới, chỉ cần chạy `alembic upgrade head`. Có thể quay lại toàn bộ
schema bằng `alembic downgrade base` trong môi trường phát triển hoặc kiểm thử.

Cài đặt frontend trong một terminal khác:

```powershell
cd frontend
npm install
```

## Chạy ứng dụng

Khởi động backend tại `http://localhost:8000`:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn weather_analysis.api.app:app --reload
```

Backend cần kết nối Internet để lấy dữ liệu dự báo, chất lượng không khí, nhiệt
độ các địa điểm và lịch sử khí hậu từ Open-Meteo. Hai tab So sánh và Lịch sử lấy
dữ liệu khí hậu qua API backend `/api/locations/{slug}/climate`; ô chọn địa điểm
lấy nhiệt độ qua `/api/locations/temperatures`. Dữ liệu dự báo và nhiệt độ được
cache trong bộ nhớ 30 phút; dữ liệu lịch sử được cache 24 giờ.

Khởi động frontend tại `http://localhost:5173` trong một terminal khác:

```powershell
cd frontend
npm run dev
```

Trang thời tiết ở `http://localhost:5173`.

Trang quản trị ở `http://localhost:5173/admin/dang-nhap`, đăng nhập bằng:

- Tên đăng nhập: `admin`
- Mật khẩu: `adminpw`

Trang quản trị cho phép tải tệp CSV mẫu và thay toàn bộ danh sách địa điểm. Tệp
phải dùng mã hóa UTF-8 và có các cột:
`name,slug,region_code,region_label,temp_offset,latitude,longitude,pin_order`.
`pin_order` có thể để trống; các cột còn lại bắt buộc có dữ liệu hợp lệ.
Tên viết tắt và tên gọi khác được quản lý trong
`backend/data/seed/location-aliases.csv` và tự động gắn theo `slug` khi nhập.
Với database đã có dữ liệu từ phiên bản cũ, chạy migration rồi nhập lại tệp mẫu
ở trang quản trị để cập nhật các tên gọi này.

## Chạy kiểm tra

Có thể chạy cả test backend và frontend trong Testing panel của VS Code. Test
e2e cần cài Playwright như hướng dẫn trên và chạy chậm hơn vì tự khởi động server.

Kiểm tra backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pyright
ruff check .
pytest -q
```

Kiểm tra frontend:

```powershell
cd frontend
npm run lint
npm run build
npm test
```

Kiểm thử giao diện:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest tests/e2e
```

Muốn quan sát trực tiếp các thao tác trong trình duyệt:

```powershell
pytest tests/e2e --headed --slowmo 500
```

Cần chạy `npm install` trong thư mục `frontend` trước khi kiểm thử giao diện.
Không cần bật sẵn ứng dụng: test tự khởi động backend và frontend trên các port
8001 và 5174, sử dụng database kiểm thử riêng rồi dọn dẹp khi kết thúc.

## Cấu trúc chính

- `backend/weather_analysis/api/`: các route FastAPI và schema trao đổi dữ liệu.
- `backend/weather_analysis/clients/`: các client gọi dịch vụ dữ liệu bên thứ ba.
- `backend/weather_analysis/services/`: nghiệp vụ xác thực, tra cứu và nhập địa điểm.
- `backend/weather_analysis/repositories/`: truy cập dữ liệu qua SQLAlchemy ORM.
- `backend/migrations/`: lịch sử thay đổi schema database bằng Alembic.
- `backend/data/seed/`: dữ liệu mẫu cho tài khoản và địa điểm.
- `backend/tests/`: unit test, API test và e2e test.
- `frontend/src/api/`: mã gọi API từ trình duyệt.
- `frontend/src/pages/`: các màn hình của ứng dụng.
- `frontend/src/components/`: các thành phần giao diện dùng lại được.

## Biến môi trường

- `WEATHER_DB_URL`: URL kết nối SQLAlchemy. Khi không đặt, ứng dụng dùng SQL Server LocalDB.
- `WEATHER_DB_NAME`: tên database LocalDB. Mặc định là `WeatherAnalysis`.
- `WEATHER_DB_DIR`: thư mục chứa tệp `.mdf` và `.ldf`. Mặc định là `backend/data`.
- `WEATHER_SESSION_SECRET`: khóa dùng để ký session cookie. Phải đặt thành một giá trị bí mật khi triển khai thật.
- `WEATHER_API_URL`: URL backend mà Vite chuyển tiếp các request `/api` tới. Mặc định là `http://localhost:8000`.

Khi dùng SQL Server thật, đặt `WEATHER_DB_URL` theo dạng
`mssql+pyodbc://user:password@server/WeatherAnalysis?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes`.
Database trên server thật cần được tạo trước khi chạy ứng dụng.
