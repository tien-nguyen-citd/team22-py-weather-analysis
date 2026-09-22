# Dịch vụ đọc câu hỏi thời tiết

Service đọc một câu hỏi tiếng Việt và trích xuất địa điểm, thời gian, hoạt động
và ý định để frontend dùng cho luồng tư vấn thời tiết. Service chạy độc lập với backend tại
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

## Đánh giá độ chính xác

```powershell
cd nlu-service
.\.venv\Scripts\Activate.ps1
python -m weather_nlu.evaluate
```

Lệnh này đọc các câu hỏi đã gán nhãn trong `data/questions.csv` rồi in ra:

- Độ chính xác tổng; một câu chỉ tính đúng khi cả bốn trường đều đúng.
- Độ chính xác theo từng trường: địa điểm, thời gian, hoạt động, ý định.
- Độ chính xác theo nhóm câu hỏi (cột `group`).
- Số câu tìm điểm đến không có từ khóa mà MiniLM nhận đúng.
- Danh sách câu sai kèm giá trị cần có và giá trị nhận được.

Nhãn thời gian được tính theo ngày 16/09/2026. Các nhóm câu hỏi:

| Nhóm | Nội dung |
| --- | --- |
| `basic` | Câu hỏi thường gặp |
| `paraphrase` | Cách nói khác, từ lóng, tên gọi khác của địa điểm |
| `place` | Câu hỏi tìm điểm đến |
| `holdout` | Câu viết sau khi chỉnh dữ liệu và không dùng để chỉnh từ khóa hay câu mẫu |

Khi sửa từ khóa hoặc câu mẫu, hãy chạy lại lệnh này để xem câu nào đúng thêm và
câu nào bị sai đi. Không chỉnh dữ liệu theo kết quả của nhóm `holdout`, để nhóm
này vẫn phản ánh độ chính xác trên câu hỏi mới.

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
| | mùa xuân, hè, thu, đông; hè này, nghỉ hè | Xuân 2–4, hè 5–7, thu 8–10, đông 11–1; chọn mùa đang diễn ra hoặc mùa gần nhất sắp tới |
| | Tết, Tết Nguyên Đán | Tháng 1–2, vì Tết âm lịch luôn rơi vào khoảng này; chọn dịp đang diễn ra hoặc sắp tới |
| | Tết dương lịch | Tháng 1 |
| | Trung thu | Tháng 9–10 |
| | năm nay, năm sau | Cả năm |
| `best_time` | tháng mấy, khi nào, mùa nào, ngày nào | Cụm thời gian khác trong câu là phạm vi tìm; không có thì không giới hạn |

Khi câu hỏi có nhiều cụm thời gian, thứ tự ưu tiên là: hỏi thời điểm tốt nhất,
khoảng thời gian cụ thể, rồi hiện tại.

## Quy ước phân loại ý định

Trường `intent` cho biết người dùng muốn tìm gì để giao diện gọi đúng API tư vấn.

| Intent | Ví dụ | Giao diện xử lý |
| --- | --- | --- |
| `find_place` | Tháng 12 đi biển ở đâu? | Xếp hạng điểm đến trong tháng |
| `find_time` | Tháng nào đi Đà Lạt đẹp? | Tư vấn thời điểm tại một địa điểm |

Service xét lần lượt các bước sau và dừng ở bước đầu tiên có kết quả:

1. Câu hỏi nêu một địa điểm trong danh mục thì là `find_time`.
2. Câu hỏi chứa từ khóa của một intent trong `data/intents.csv` thì lấy intent
   đó. Ví dụ "ở đâu", "tỉnh nào" là `find_place`; "thế nào", "có ổn không" là
   `find_time`. Từ khóa được so khớp như từ khóa hoạt động: "đâu" không khớp với
   "đầu" khi câu có dấu, câu gõ không dấu vẫn khớp.
3. Câu hỏi tìm thời điểm tốt nhất (`best_time`), ví dụ "tháng mấy", "khi nào",
   thì là `find_time`.
4. Các câu còn lại được so với câu mẫu trong `data/intent-examples.csv` theo
   embedding MiniLM. 3 câu mẫu gần nghĩa nhất bỏ phiếu (k-NN, k=3); khi hòa
   phiếu, câu mẫu gần nhất thắng.

**Thứ tự dòng trong `data/intents.csv` là thứ tự ưu tiên.** Khi câu hỏi có từ
khóa của nhiều intent, ví dụ "Tháng 12 đi đâu thì có hợp không?", intent đứng
trước (`find_place`) thắng.

Trước khi so sánh embedding, tên địa điểm và các cụm từ khóa hoạt động như "chạy
marathon", "chụp ảnh" được bỏ khỏi câu hỏi. Nhờ vậy MiniLM tập trung vào dạng câu
hỏi thay vì chủ đề của câu. Mỗi câu mẫu có thêm một bản không dấu để nhận ra câu
hỏi gõ không dấu. Câu hỏi của người dùng thì giữ nguyên.

Khi không đọc được câu hỏi, service trả `find_time`. Mỗi câu hỏi được encode tối
đa một lần; vector này dùng chung cho cả hoạt động và ý định.

Để thêm một intent mới:

1. Thêm một dòng vào `data/intents.csv` với `id`, `name` và các từ khóa cách nhau
   bằng dấu `;`. Có thể để trống cột từ khóa.
2. Thêm giá trị tương ứng vào `Intent` trong `weather_nlu/question_info.py`.
3. Thêm câu mẫu vào `data/intent-examples.csv`, nên có cả câu không chứa từ khóa.
4. Gán nhãn intent cho các câu liên quan trong `data/questions.csv` rồi chạy
   `python -m weather_nlu.evaluate` và `pytest -m model` để kiểm tra độ chính xác.

## Dữ liệu dùng chung và giới hạn

- Địa điểm được nhận ra bằng cách tra tên và tên gọi khác, ví dụ SG, Sài Thành,
  Thủ đô, ĐL, đảo ngọc. Địa điểm ngoài danh mục như Côn Đảo, Cát Bà, Sầm Sơn hoặc
  Fansipan không được nhận ra. Khi đó API
  dùng `currentLocationSlug` và trả `locationFromQuestion: false`.
- Service đọc `backend/data/seed/locations.csv` và
  `backend/data/seed/location-aliases.csv`. Danh sách địa điểm do quản trị viên
  nhập trong ứng dụng không tự động cập nhật cho service.
- Service chỉ đọc một câu hỏi mỗi lần và không có ngữ cảnh hội thoại.
- Cấu hình `rule+minilm` ưu tiên từ khóa hoạt động; MiniLM chỉ được dùng khi câu
  hỏi không chứa từ khóa đã biết.

## Thử nghiệm model embedding

Đã thử ba model embedding trên 179 câu hỏi của `data/questions.csv` (trước khi có
nhóm `holdout`), cùng một cách xử lý như trên:

| Model | Dung lượng | Hoạt động | Intent | Chính xác tổng | Encode 1 câu |
| --- | --- | --- | --- | --- | --- |
| paraphrase-multilingual-MiniLM-L12-v2 (đang dùng) | 0,22 GB | 155/179 | 179/179 | 0,855 | ~1 ms |
| paraphrase-multilingual-mpnet-base-v2 | 1 GB | 154/179 | 176/179 | 0,821 | ~5 ms |
| multilingual-e5-large | 2,24 GB | 170/179 | 179/179 | 0,911 | ~150 ms |

Dòng MiniLM được đo lại sau khi bổ sung tên gọi khác cho địa điểm và vài câu mẫu
du lịch; hai dòng còn lại được đo trước các thay đổi này nên chỉ dùng để so sánh
tương đối.

- Service chọn MiniLM vì nhẹ và nhanh, chạy tốt trên máy cá nhân.
- e5-large chính xác hơn nhưng cần 2–3 GB RAM. Đây là hướng nâng cấp khi máy chạy
  có đủ RAM: chỉ cần đổi tên model và thêm tiền tố `"query: "` vào mỗi câu trước
  khi encode.
