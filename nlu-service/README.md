# Dịch vụ đọc câu hỏi thời tiết

Service đọc một câu hỏi tiếng Việt và trích xuất địa điểm, thời gian và hoạt động
để frontend dùng cho luồng tư vấn thời tiết. Service chạy độc lập với backend tại
port `8002` và không lưu ngữ cảnh giữa các câu hỏi.

## Cài đặt

```powershell
cd nlu-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m weather_nlu.download
```

Lần tải đầu cần kết nối Internet. Model MiniLM có dung lượng khoảng 130 MB và
được lưu trong `nlu-service/.models`. Xóa thư mục này để giải phóng dung lượng;
lần chạy sau service sẽ tải lại model.

## Chạy service

```powershell
cd nlu-service
.\.venv\Scripts\Activate.ps1
uvicorn weather_nlu.api.app:app --port 8002 --reload
```

Mở `http://localhost:8002/docs` để thử API. Service cung cấp hai endpoint:

- `POST /nlu/understand`: đọc một câu hỏi, không nhớ câu trước.
- `GET /nlu/health`: trả tình trạng sau khi model đã nạp xong.

Ví dụ request:

```json
{
  "question": "Mùa này đi Phú Quốc có hợp không?",
  "currentLocationSlug": "ha-noi",
  "today": "2026-09-20"
}
```

`currentLocationSlug` được dùng khi câu hỏi không nêu địa điểm trong danh mục.
`today` có thể bỏ trống; service sẽ lấy ngày hiện tại theo giờ Việt Nam.

## Chạy kiểm tra

```powershell
cd nlu-service
.\.venv\Scripts\Activate.ps1
pyright
ruff check .
pytest -q
pytest -m model
```

`pytest -q` không chạy test cần model. Hãy chạy `python -m weather_nlu.download`
trước khi chạy `pytest -m model`.

## Quy ước diễn giải thời gian

| Loại | Ví dụ | Khoảng thời gian |
| --- | --- | --- |
| `now` | lúc này, bây giờ, hiện tại, đang | Không có khoảng |
| `dates` | hôm nay, chiều nay | Hôm nay |
| | mai, ngày mai | Ngày mai |
| | ngày kia, ngày mốt | 2 ngày sau |
| | 3 ngày tới, mấy ngày tới | Từ ngày mai, "mấy/vài ngày" tính là 3 ngày |
| | cuối tuần (này) | Thứ Bảy và Chủ nhật tuần này, bỏ ngày đã qua |
| | tuần sau, cuối tuần sau | Thứ Hai đến Chủ nhật tuần sau, hoặc thứ Bảy và Chủ nhật tuần sau |
| | 20/10 | Ngày đó; ngày đã qua trong năm được hiểu là năm sau |
| `months` | tháng này, tháng sau, tháng 12 | Cả tháng; tháng đã qua trong năm được hiểu là năm sau |
| | mùa này | Tháng hiện tại và 2 tháng tiếp theo |
| | mùa xuân, hè, thu, đông | Xuân 2–4, hè 5–7, thu 8–10, đông 11–1; chọn mùa đang diễn ra hoặc mùa gần nhất sắp tới |
| | năm nay, năm sau | Cả năm |
| `best_time` | tháng mấy, khi nào, mùa nào, ngày nào | Cụm thời gian khác trong câu là phạm vi tìm; không có thì không giới hạn |

Khi câu hỏi có nhiều cụm thời gian, thứ tự ưu tiên là: hỏi thời điểm tốt nhất,
khoảng thời gian cụ thể, rồi hiện tại.

## Dữ liệu dùng chung và giới hạn

- Địa điểm được nhận ra bằng cách tra tên và tên gọi khác. Địa điểm ngoài danh
  mục như Côn Đảo, Cát Bà, Sầm Sơn hoặc Fansipan không được nhận ra. Khi đó API
  dùng `currentLocationSlug` và trả `locationFromQuestion: false`.
- Service đọc `backend/data/seed/locations.csv` và
  `backend/data/seed/location-aliases.csv`. Danh sách địa điểm do quản trị viên
  nhập trong ứng dụng không tự động cập nhật cho service.
- Service chỉ đọc một câu hỏi mỗi lần và không có ngữ cảnh hội thoại.
- Cấu hình `rule+minilm` ưu tiên từ khóa hoạt động; MiniLM chỉ được dùng khi câu
  hỏi không chứa từ khóa đã biết.
