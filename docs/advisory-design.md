# Tư vấn thời điểm theo hoạt động

Module nhận **địa điểm, khoảng tháng và hoạt động**, trả về tối đa ba thời điểm
đáng cân nhắc cùng số liệu lịch sử và cách tính điểm. Kết quả phục vụ lựa chọn
thời điểm ở mức tháng hoặc đầu/giữa/cuối tháng, không dự báo cho ngày cụ thể.

## Phạm vi

- Chọn thời điểm tại một địa điểm có trong danh mục của ứng dụng.
- Dùng lượng mưa ngày và nhiệt độ trung bình ngày đã lưu trong `daily_weather`.
- Chưa chọn địa điểm, tư vấn giờ/ngày, lập lịch nhiều ngày liên tiếp hoặc nối chatbot.
- Backend không phụ thuộc package hoặc model ML trong `chatbot/`.

## Đầu vào và ứng viên

| Trường JSON | Ý nghĩa | Mặc định |
| --- | --- | --- |
| `locationSlug` | Slug địa điểm trong danh mục | Bắt buộc |
| `time.startMonth` | Tháng bắt đầu, `YYYY-MM` | Khi bỏ cả `time`: tháng kế tiếp |
| `time.endMonth` | Tháng kết thúc, `YYYY-MM` | Khi bỏ cả `time`: đủ 12 tháng kể từ tháng bắt đầu |
| `activityId` | Mã hoạt động | `general` |
| `topK` | Số đề xuất, số nguyên từ 1 đến 3 | `3` |

`time` và `activityId` có thể là `null`. Nếu truyền `time`, phải có đủ hai tháng.
Khoảng tìm kiếm gồm cả tháng đầu và tháng cuối, từ 1 đến 12 tháng liên tiếp,
có thể qua năm. Tháng không hợp lệ, thứ tự đảo ngược, hoạt động lạ hoặc trường
ngoài contract đều bị từ chối. Không tự đổi địa điểm không tồn tại sang địa điểm khác.

- Khoảng 3–12 tháng: mỗi tháng là một ứng viên.
- Khoảng 1–2 tháng: mỗi tháng có ba ứng viên, ngày 1–10, 11–20, 21–cuối tháng.
- Các ứng viên không chồng lấn và không vượt phạm vi yêu cầu.

Ví dụ: `2027-12` đến `2028-01` tạo sáu giai đoạn. Muốn xem chi tiết một tháng
đang được đề xuất, gửi lại yêu cầu với tháng bắt đầu và kết thúc cùng là tháng đó.

Ngày tham chiếu được truyền vào service để dễ kiểm thử. API dùng ngày hiện tại
theo múi giờ Việt Nam. Năm trong đầu vào xác định nhãn lịch của ứng viên; các số
liệu lấy từ cùng tháng/giai đoạn trong lịch sử, không phải dự báo riêng cho năm đó.

## Tiêu chí và công thức

Các giá trị dưới đây là **quy ước sản phẩm**, không phải chuẩn khí tượng hoặc
ngưỡng bảo đảm an toàn. Cấu hình tập trung tại
`backend/weather_analysis/advisory/activities.py`.

| Mã | Hoạt động | Mưa / nhiệt độ | Khoảng nhiệt độ ưu tiên |
| --- | --- | --- | --- |
| `general` | Nhu cầu chung | 60% / 40% | 20–28°C |
| `travel` | Du lịch | 60% / 40% | 20–28°C |
| `wedding` | Đám cưới | 80% / 20% | 20–28°C |
| `running` | Chạy bộ, thể thao ngoài trời | 40% / 60% | 16–24°C |
| `photography` | Chụp ảnh ngoài trời | 90% / 10% | 18–30°C |
| `coffee` | Cà phê ngoài trời | 60% / 40% | 20–28°C |
| `beach` | Tắm biển | 60% / 40% | 25–31°C |
| `camping` | Cắm trại, leo núi, dã ngoại | 80% / 20% | 18–26°C |
| `drying` | Phơi quần áo | 100% / 0% | Không chấm |

Với mỗi ngày trong ứng viên lịch sử:

1. Điểm ít mưa bằng 100 nếu lượng mưa **dưới 1 mm**, bằng 0 nếu từ 1 mm trở lên.
2. Điểm nhiệt độ bằng 100 trong khoảng ưu tiên. Ngoài khoảng, trừ 10 điểm cho
   mỗi °C cách biên gần nhất, tối thiểu bằng 0.
3. Lấy trung bình từng thành phần trong mỗi năm, rồi trung bình đều 10 năm.
4. Điểm tổng = điểm ít mưa × trọng số mưa + điểm nhiệt độ × trọng số nhiệt độ.

Phơi quần áo không có điểm nhiệt độ (`temperatureScore: null`), đóng góp nhiệt độ
bằng 0. Nhiệt độ trung bình vẫn được trả để tham khảo.

Điểm dùng thang cố định 0–100, không chuẩn hóa theo những ứng viên khác. Việc thêm
một tháng vào danh sách không làm đổi điểm của tháng cũ. Khi đổi độ phân giải từ
tháng sang giai đoạn, tập ngày được phân tích thay đổi nên điểm có thể khác.

### Ví dụ tính tay

Giả sử trong **mỗi năm** của 10 năm lịch sử, giai đoạn 1–10/1 có:

- Năm ngày mưa 0,8 mm/ngày, năm ngày mưa 1 mm/ngày.
- Nhiệt độ trung bình của mọi ngày là 26°C.

Với đám cưới:

- Điểm ít mưa: `5 / 10 × 100 = 50`.
- Điểm nhiệt độ: `100`, vì 26°C nằm trong 20–28°C.
- Điểm tổng: `50 × 0,8 + 100 × 0,2 = 60`.
- Tỷ lệ ngày mưa từ 1 mm: `50%`; lượng mưa trung bình: `0,9 mm/ngày`.
- Mẫu phân tích: 100 ngày thuộc 10 năm.

Đây là dữ liệu minh họa được kiểm chứng bằng unit test, không phải thống kê thực
tế của một địa điểm. “60 điểm” không có nghĩa là 60% khả năng trời đẹp.

### Xếp hạng và lời giải thích

- Điểm tổng giảm dần; hòa điểm thì tỷ lệ ngày mưa thấp hơn đứng trước, rồi ngày bắt đầu sớm hơn.
- Tính và xếp hạng bằng số chưa làm tròn. JSON giữ số tính toán; lời giải thích làm tròn một chữ số thập phân.
- Ứng viên khác cách điểm cao nhất dưới 3 điểm có `similarToBest: true`.
- Điểm cao nhất dưới 50 có `lowSuitability: true`, vẫn trả các lựa chọn đứng đầu trong phạm vi yêu cầu.
- `recommendations` theo thứ hạng; `candidates` chứa toàn bộ ứng viên theo thời gian, mỗi ứng viên có `rank`.
- Lời giải thích được dựng từ số liệu và trọng số bằng mẫu tiếng Việt, không dùng LLM.

## Dữ liệu và ranh giới module

Service `get_advice(session, request, client, today)` thực hiện:

1. Chuẩn hóa yêu cầu, xác nhận hoạt động và tìm địa điểm.
2. Lấy baseline từ `calculate_climate_period(today)`.
3. Gọi `get_location_climate` hiện có để nạp và kiểm tra lịch sử.
4. Đọc các dòng ngày trong baseline qua `AdvisoryWeatherRepository`.
5. Kiểm tra dữ liệu, tạo ứng viên, tính điểm, xếp hạng và diễn giải.

Baseline gồm 10 năm đứng trước 12 tháng gần nhất đã hoàn tất và có dữ liệu theo
quy tắc độ trễ ERA5 hiện có. Ví dụ, ngày tham chiếu 20/09/2026 cho baseline
01/09/2015–31/08/2025; dữ liệu 09/2025–08/2026 không tham gia chấm điểm.
Mỗi tháng có đủ 10 lần xuất hiện, dù baseline không bắt đầu vào tháng 1.

Ngày 29/2 phải có mặt nếu nằm trong dữ liệu lịch sử cần kiểm tra, nhưng bị loại
khỏi phép tính. Cuối tháng 2 được chấm bằng các ngày 21–28 ở mọi năm; nhãn ứng
viên vẫn kết thúc vào 29/2 nếu năm người dùng chọn là năm nhuận.

Thiếu ngày, trùng ngày, số không hữu hạn hoặc lượng mưa âm đều gây lỗi. Không
bù dữ liệu, coi ngày thiếu là ít mưa hoặc giảm số năm phân tích. Nhiệt độ và lượng
mưa trả về cũng được lấy trung bình theo năm; lượng mưa là **mm/ngày**, tỷ lệ
ngày mưa là **phần trăm 0–100**. `sampleDays` không gồm ngày 29/2.

Repository tư vấn chỉ đọc. Luồng khí hậu hiện có có thể ghi dữ liệu mới vào
database; giao dịch API được commit khi thành công và rollback khi lỗi. Với địa
điểm chưa có dữ liệu, lần đầu có thể phải nạp khoảng 11 năm lịch sử và mất thời
gian chờ nhà cung cấp (timeout archive hiện là 45 giây). Những lần sau dùng lại
database, chỉ nạp phần còn thiếu theo hành vi của service khí hậu.

Module không đổi schema database, client Open-Meteo, công thức chấm điểm cũ hoặc
package chatbot. Các kiểu nghiệp vụ là dataclass; schema HTTP nằm riêng trong
API. Các hàm tạo ứng viên, tính điểm, xếp hạng và diễn giải không gọi mạng/database.

## Thử qua API

Khởi động backend theo README, mở `http://localhost:8000/docs`, nhóm `advisory`.
Không cần đăng nhập cho hai endpoint tư vấn.

### Danh mục

`GET /api/advisory/activities` trả chín cấu hình, gồm `general`. Mỗi cấu hình có
mã, tên, trọng số dạng 0–1, khoảng nhiệt độ, ngưỡng mưa và mô tả tiếng Việt.
Endpoint này không nạp lịch sử hoặc gọi nhà cung cấp.

### Tư vấn

`POST /api/advisory`, ví dụ tìm giai đoạn cho đám cưới:

```json
{
  "locationSlug": "ha-noi",
  "time": {"startMonth": "2027-01", "endMonth": "2027-01"},
  "activityId": "wedding",
  "topK": 3
}
```

Để tìm 12 tháng mặc định, chỉ cần gửi:

```json
{"locationSlug": "ha-noi"}
```

Response có `request` đã chuẩn hóa, `baselineStart`, `baselineEnd`, `activity`,
`recommendations`, `candidates`, `summary`, `lowSuitability` và `notes`.
Một ứng viên trong response, **rút gọn từ ví dụ tính tay ở trên**:

```json
{
  "window": {
    "startDate": "2027-01-01",
    "endDate": "2027-01-10",
    "label": "Đầu tháng 01/2027",
    "resolution": "period"
  },
  "temperatureMean": 26.0,
  "rainyDayPercentage": 50.0,
  "precipitationMean": 0.9,
  "rainScore": 50.0,
  "temperatureScore": 100.0,
  "rainContribution": 40.0,
  "temperatureContribution": 20.0,
  "score": 60.0,
  "sampleYears": 10,
  "sampleDays": 100,
  "rank": 1,
  "similarToBest": false
}
```

Ứng viên còn có `explanation` giải thích các số trên bằng tiếng Việt. Response
thực tế phụ thuộc lịch sử của địa điểm, không cố định theo ví dụ minh họa.

| HTTP | Tình huống |
| --- | --- |
| 200 | Có kết quả, kể cả khi mức phù hợp thấp |
| 422 | Sai cấu trúc, khoảng tháng, hoạt động hoặc số lựa chọn |
| 404 | Không tìm thấy địa điểm |
| 502 | Lỗi nhà cung cấp hoặc dữ liệu lịch sử thiếu/không hợp lệ |

Lỗi có dạng `{"detail": "Thông báo tiếng Việt"}`. Không trả bảng xếp hạng một phần
khi không đủ dữ liệu. Các lỗi cấu trúc chỉ được chuyển thông báo trong router tư
vấn, không thay đổi hành vi validation của các API cũ.

## Kiểm thử

Từ thư mục `backend`, với môi trường Python của dự án:

```powershell
python -m pytest tests/unit/test_advisory.py tests/unit/test_advisory_service.py tests/api/test_advisory_routes.py -q
pyright
ruff check .
python -m pytest -q
```

Test dùng nhà cung cấp giả lập và database kiểm thử riêng theo fixture hiện có,
không gọi Open-Meteo. Bao phủ công thức tính tay, đổi hoạt động làm đổi thứ hạng,
điểm độc lập với tập ứng viên, năm nhuận, ranh giới tháng, dữ liệu thiếu/sai,
baseline 10 năm, nạp lần đầu, dùng lại lịch sử, contract JSON và lỗi API.

## Giới hạn diễn giải

- Nhiệt độ trung bình ngày không thể hiện mọi khung giờ hoặc nhiệt độ cực đại.
- Mưa dưới 1 mm không đồng nghĩa với hoàn toàn không mưa.
- Điểm cao nhất chỉ là lựa chọn đứng đầu theo tiêu chí trong phạm vi đã hỏi.
- Lịch sử khí hậu không khẳng định thời tiết vào ngày tổ chức sự kiện.
- Không suy ra ánh sáng đẹp, an toàn tắm biển, điều kiện leo núi hoặc tốc độ khô
  của quần áo khi thiếu các biến liên quan.
