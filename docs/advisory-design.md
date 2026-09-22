# Tư vấn thời điểm theo hoạt động

Module nhận **địa điểm, khoảng tháng và hoạt động**, trả về tối đa ba thời điểm
đáng cân nhắc cùng số liệu lịch sử và cách tính điểm. Kết quả phục vụ lựa chọn
thời điểm ở mức tháng hoặc đầu/giữa/cuối tháng, không dự báo cho ngày cụ thể.

## Phạm vi

- Chọn thời điểm tại một địa điểm có trong danh mục của ứng dụng.
- Dùng lượng mưa ngày và nhiệt độ trung bình ngày đã lưu trong `daily_weather`.
- Chưa tư vấn giờ/ngày hoặc lập lịch nhiều ngày liên tiếp. Giao diện Tư vấn mới
  nhận câu hỏi tự do qua `nlu-service` rồi quy về đầu vào theo tháng của module.
- Backend không phụ thuộc package hoặc model ML trong `chatbot/`.

## Nối với nlu-service

Trang Tư vấn luôn mở khung hỏi đáp khi tải. Câu hỏi được gửi tới
`POST /nlu/understand` cùng vị trí người dùng và ngày tham chiếu theo giờ Việt Nam.
Nếu không kết nối được dịch vụ hoặc lời gọi thất bại, khung hỏi đáp vẫn giữ nguyên
và hiện thông báo lỗi kèm gợi ý điền form. Luồng `/api/advisory` qua form vẫn hoạt
động bình thường khi dịch vụ NLU gián đoạn.

Kết quả đọc câu hỏi có trường `intent` để giao diện chọn API tư vấn:

- `find_place`, ví dụ "Tháng 12 đi biển ở đâu?": gọi `/api/advisory/destinations`
  để xếp hạng điểm đến. Tháng là tháng bắt đầu khi câu hỏi nêu ngày hoặc tháng,
  tháng hiện tại khi hỏi lúc này, còn lại là tháng kế tiếp. Câu không nêu hoạt
  động thì dùng Du lịch.
- `find_time`, ví dụ "Tháng nào đi Đà Lạt đẹp?": gọi `/api/advisory` để tìm thời
  điểm phù hợp tại một địa điểm như mô tả bên dưới. Giá trị `intent` lạ cũng đi
  theo luồng này.

Vị trí người dùng là thiết lập chung, độc lập với địa điểm thời tiết đang xem. URL
chỉ chứa tên trang; địa điểm đang xem nằm trong history state, không có thì dùng vị
trí người dùng. Giao diện lưu slug địa điểm trong trình duyệt và cho tìm kiếm hoặc định vị lại
ở góc phải header. Lần đầu chưa có thiết lập, trình duyệt dùng GPS để chọn địa điểm
gần nhất trong danh mục; nếu không định vị được thì dùng Hà Nội. Tọa độ
GPS thô không được lưu hoặc gửi tới backend và NLU.

Kết quả thời gian từ dịch vụ được quy về khoảng tháng như sau:

| Loại thời gian | Khoảng tháng gửi tới `/api/advisory` |
| --- | --- |
| Không có | 12 tháng kể từ tháng kế tiếp |
| `now` | Tháng hiện tại |
| `dates` | Tháng của ngày bắt đầu đến tháng của ngày kết thúc |
| `months` | Tháng bắt đầu đến tháng kết thúc |
| `best_time` không giới hạn | 12 tháng kể từ tháng kế tiếp |
| `best_time` có giới hạn | Tháng bắt đầu đến tháng kết thúc |

Nếu thiếu một đầu khoảng thời gian, mốc còn lại được dùng cho cả hai đầu. Khoảng
dài hơn 12 tháng được cắt còn 12 tháng đầu. Địa điểm không có trong câu hỏi dùng
vị trí người dùng đã lưu. Hoạt động nói rõ trong câu luôn được ưu tiên. Nếu câu
chỉ nêu một địa điểm có hoạt động đặc trưng đã cấu hình, giao diện dùng hoạt động
đó làm gợi ý: Vũng Tàu, Bà Rịa–Vũng Tàu, Nha Trang, Phan Thiết và Phú Quốc gợi
ý tắm biển. Các địa điểm khác dùng nhu cầu chung để ưu tiên ít mưa và nhiệt độ
trung bình ngày 20–28°C. Vị trí mặc định không được dùng để tự suy ra hoạt động
khi câu hỏi không nhắc địa điểm.

`now` và `dates` hiện vẫn được phân tích bằng lịch sử khí hậu của tháng tương ứng,
không dùng dữ liệu thời tiết hiện tại hoặc dự báo ngày. Vì vậy kết quả không phải
câu trả lời dự báo chính xác cho hôm nay hay một ngày cụ thể.

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
| `travel` | Du lịch | 60% / 40% | 16–28°C |
| `wedding` | Tổ chức đám cưới | 80% / 20% | 20–28°C |
| `sports` | Thể thao ngoài trời | 80% / 20% | 16–30°C |
| `photography` | Chụp ảnh ngoài trời | 90% / 10% | 18–30°C |
| `beach` | Tắm biển | 30% / 70% | 28–34°C |
| `camping` | Cắm trại, dã ngoại | 90% / 10% | 10–26°C |
| `construction` | Thi công xây dựng | 80% / 20% | 15–30°C |
| `outdoor_event` | Sự kiện ngoài trời | 70% / 30% | 20–28°C |

Tắm biển đặt nặng nhiệt độ vì trời lạnh thì không xuống biển được dù khô ráo. Ví
dụ tháng 12, biển miền Bắc ít mưa nhưng nhiệt độ trung bình khoảng 19°C nên bị điểm
thấp, xếp sau các bãi biển phía Nam.

Form tìm địa điểm không hiện `construction` vì thi công gắn với công trình có sẵn,
không phải việc chọn nơi để đi.

Với mỗi ứng viên lịch sử:

1. Một ngày là **ngày mưa** nếu lượng mưa từ 10 mm trở lên. Ngưỡng 10 mm theo chỉ
   số R10mm (ngày mưa lớn) do ETCCDI định nghĩa: mức mưa đủ gây ảnh hưởng đáng kể
   tới kế hoạch ngoài trời, thay vì mọi cơn mưa phùn.
2. Tỷ lệ ngày mưa và điểm nhiệt độ theo ngày được lấy trung bình trong mỗi năm,
   rồi trung bình đều 10 năm.
3. Điểm ít mưa bằng 100 khi tỷ lệ ngày mưa **không quá 10%** (khoảng 3 ngày mỗi
   tháng). Vượt mức này, trừ 2,5 điểm cho mỗi 1%, nên từ 50% ngày mưa trở lên
   điểm ít mưa bằng 0. Mức phạt cao để tháng mùa mưa tụt điểm rõ rệt thay vì chỉ
   giảm nhẹ.
4. Điểm nhiệt độ của một ngày bằng 100 trong khoảng ưu tiên. Ngoài khoảng, trừ 10
   điểm cho mỗi °C cách biên gần nhất, tối thiểu bằng 0.
5. Điểm tổng = điểm ít mưa × trọng số mưa + điểm nhiệt độ × trọng số nhiệt độ.

Điểm dùng thang cố định 0–100, không chuẩn hóa theo những ứng viên khác. Việc thêm
một tháng vào danh sách không làm đổi điểm của tháng cũ. Khi đổi độ phân giải từ
tháng sang giai đoạn, tập ngày được phân tích thay đổi nên điểm có thể khác.

### Ví dụ tính tay

Giả sử trong **mỗi năm** của 10 năm lịch sử, giai đoạn 1–10/1 có:

- Bảy ngày mưa 9,8 mm/ngày, ba ngày mưa 10 mm/ngày.
- Nhiệt độ trung bình của mọi ngày là 26°C.

Với đám cưới:

- Tỷ lệ ngày mưa từ 10 mm: `3 / 10 = 30%`.
- Điểm ít mưa: `100 − (30 − 10) × 2,5 = 50`.
- Điểm nhiệt độ: `100`, vì 26°C nằm trong 20–28°C.
- Điểm tổng: `50 × 0,8 + 100 × 0,2 = 60`.
- Lượng mưa trung bình: `9,86 mm/ngày`.
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

## Demo trên web

Sau khi chạy backend và frontend theo README, mở
`http://localhost:5173/tu-van` hoặc chọn tab **Tư vấn** trong ứng dụng.

1. Chọn vị trí người dùng ở header hoặc nêu địa điểm trong câu hỏi. Khi dùng form,
   chọn chế độ **Tìm thời điểm** rồi chọn địa điểm, hoạt động và khoảng tháng.
2. Nhấn **Tìm thời điểm phù hợp** để xem đề xuất chính và tối đa hai lựa chọn thay thế.
3. Mở **Vì sao chọn?** để xem số liệu và đóng góp của từng tiêu chí vào điểm tổng.
4. Chọn một cột trên biểu đồ để xem số liệu của ứng viên đó; hỗ trợ Tab và Enter.
   Các cột xếp theo tháng 1 → 12 và không ghi năm, vì điểm được tính từ lịch sử khí
   hậu chứ không phụ thuộc năm.
5. Với ứng viên theo tháng, chọn **Xem giai đoạn trong tháng này** để phân tích đầu,
   giữa và cuối tháng.

Để tìm nơi nên đi, chọn chế độ **Tìm địa điểm** trong form, chọn tháng và hoạt động
rồi nhấn **Tìm địa điểm phù hợp** để xem bảng xếp hạng điểm đến.

Ba mẫu điền nhanh gồm đám cưới tại TP.HCM, du lịch Phú Quốc và cắm trại Đà Lạt.
Mẫu chỉ điền địa điểm, hoạt động và 12 tháng mặc định; kết quả luôn lấy từ API,
không gắn cứng thời điểm thắng. Mẫu được ẩn nếu địa điểm không còn trong danh mục.

Danh mục và tiêu chí lấy từ backend. Kết quả được cache theo toàn bộ yêu cầu;
đổi đầu vào sẽ ẩn kết quả cũ và hủy chờ request cũ. Lỗi dự báo hiện tại không chặn
tư vấn từ lịch sử. Lần đầu tải lịch sử có thông báo chờ và lỗi có nút thử lại.

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
  "rainyDayPercentage": 30.0,
  "precipitationMean": 9.86,
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
- Mưa dưới 10 mm không đồng nghĩa với không mưa, chỉ là mưa nhỏ.
- Tổng mưa theo ngày không cho biết mưa rơi vào giờ nào.
- Điểm cao nhất chỉ là lựa chọn đứng đầu theo tiêu chí trong phạm vi đã hỏi.
- Lịch sử khí hậu không khẳng định thời tiết vào ngày tổ chức sự kiện.
- Không suy ra ánh sáng đẹp, an toàn tắm biển hoặc điều kiện leo núi khi thiếu
  các biến liên quan.
