# Đánh giá đề tài và bốn tab Nắng Mưa

Phạm vi: bốn tab đang hoạt động trong frontend — **Tổng quan**, **Khung giờ tốt**, **So sánh** và **Lịch sử**. Nhận xét dựa trên mã nguồn hiện tại và bản mô tả thiết kế; phần hiển thị chưa được kiểm tra trực quan bằng trình duyệt trong lần đánh giá này.

## 1. Vì sao chọn đề tài này? Nó giúp ích gì cho người dùng?

Người dùng thường cần một quyết định cụ thể như “nên ra ngoài lúc nào?”, “giờ nào phù hợp để chạy bộ?” hoặc “tháng nào nên đến địa điểm này?”. Các con số nhiệt độ, mưa, UV và gió đứng riêng lẻ chưa trả lời trực tiếp những câu hỏi đó. Nắng Mưa được xây dựng để tổng hợp dữ liệu thời tiết thành nhận định, khung giờ gợi ý và phép so sánh dễ đọc.

Giá trị mà phiên bản hiện tại mang lại:

- **Ra quyết định nhanh trong ngày:** xem thời tiết hiện tại, điểm theo giờ, nhận định và dự báo bảy ngày tại một nơi.
- **Lên kế hoạch theo hoạt động:** xem khung giờ gợi ý riêng cho chạy bộ, chụp ảnh ngoài trời, cà phê ngoài trời và phơi quần áo.
- **Chọn điểm đến và thời điểm:** so sánh khí hậu trung bình của hai địa điểm theo từng tháng.
- **Hiểu bối cảnh thời tiết gần đây:** đối chiếu lượng mưa của 12 tháng trọn vẹn gần nhất với mức trung bình 10 năm trước.
- **Theo dõi địa điểm quan tâm:** tìm kiếm địa điểm và lưu các địa điểm thường xem để chuyển nhanh giữa chúng.

Ứng dụng dùng dữ liệu dự báo và dữ liệu lịch sử từ Open-Meteo. Các **điểm thuận lợi** và **điểm du lịch** là quy tắc gợi ý do sản phẩm tính toán, không phải xác suất thời tiết hay cam kết rằng một hoạt động sẽ an toàn hoặc thuận lợi.

## 2. Ưu điểm và nhược điểm của từng tab

### 2.1. Tổng quan

**Ưu điểm**

- Gom nhiệt độ, độ ẩm, gió, khả năng mưa và UV vào một màn hình; người dùng không cần mở nhiều nguồn để nắm tình hình cơ bản.
- Có nhận định bằng câu chữ, biểu đồ điểm 24 giờ, khung giờ gợi ý, chi tiết trong ngày và dự báo bảy ngày. Cách trình bày đi từ thông tin nhanh đến chi tiết.
- Có phần giải thích các yếu tố, trạng thái tải/lỗi và nút thử lại. Biểu đồ giờ có thể cuộn ngang trên màn hình nhỏ.

**Nhược điểm**

- Mô tả điều kiện được suy ra bằng quy tắc đơn giản. Ví dụ, câu “chiều có mưa rào” không kiểm tra mưa có thực sự rơi vào buổi chiều.
- Khi thiếu dữ liệu, một số giá trị mặc định vẫn hiện như số thật, chẳng hạn nhiệt độ, độ ẩm, gió và điểm sương. Đây là nhược điểm cần ưu tiên sửa vì ảnh hưởng đến độ tin cậy.

### 2.2. Khung giờ tốt

**Ưu điểm**

- Biểu đồ 24 giờ cho thấy giờ nào thuận lợi hơn, giúp người dùng so sánh nhiều khoảng thời gian trong cùng ngày.
- Bốn hoạt động có quy tắc chấm riêng, nên gợi ý cụ thể hơn điểm thời tiết chung. Nếu không có khung giờ đạt ngưỡng, thẻ hoạt động nêu rõ điều đó.
- Điểm, khoảng giờ và ghi chú được đặt trong cùng một thẻ; người dùng có thể đọc nhanh mà không cần thao tác thêm.

**Nhược điểm**

- Hiện chỉ phân tích **hôm nay** và bốn hoạt động cố định; chưa chọn được ngày khác hoặc điều chỉnh sở thích cá nhân.
- Một số quy tắc mới là xấp xỉ: “giờ vàng” chụp ảnh dùng mốc 07:00/17:00 cố định thay vì giờ mặt trời mọc/lặn tại địa điểm; gợi ý phơi quần áo chưa dùng độ ẩm dù ghi chú nói cần độ ẩm thấp.
- Chi tiết của cột giờ chủ yếu xuất hiện khi rê chuột, nên khó xem trên thiết bị cảm ứng và khi dùng bàn phím.

### 2.3. So sánh

**Ưu điểm**

- Người dùng chọn hai địa điểm và một tháng; hai thẻ điểm, ba chỉ số khí hậu và câu kết luận cùng cập nhật theo lựa chọn.
- Biểu đồ 12 tháng giúp nhìn tính mùa vụ và có thể bấm vào tháng để xem chi tiết, hữu ích khi chưa chốt thời điểm đi.
- Nhiệt độ, lượng mưa và số ngày mưa được tính từ dữ liệu lịch sử theo từng địa điểm thay vì bảng số liệu giả theo vùng. Có trạng thái tải, lỗi và thử lại.

**Nhược điểm**

- “Điểm du lịch” chỉ dùng **nhiệt độ trung bình tháng và số ngày mưa** theo một ngưỡng phù hợp cố định. Điểm chưa xét cường độ mưa, nắng, gió, nhu cầu của từng người hoặc chi phí chuyến đi.
- Các con số là **trung bình khí hậu 10 năm**, phù hợp để tham khảo mùa đi; chúng không dự báo thời tiết của một ngày hay chuyến đi sắp tới. Câu khuyến nghị cần được hiểu trong giới hạn này.
- Hai ô chọn vẫn cho phép chọn cùng một địa điểm ở cả hai bên, tạo ra phép so sánh ít giá trị. Nếu đổi địa điểm ở thanh chung khi tab đang mở, địa điểm A có thể giữ lựa chọn cũ, dễ gây nhầm giữa địa điểm chung và địa điểm so sánh.
- Danh sách chọn địa điểm dài; tìm một địa điểm trong ô `select` mặc định có thể mất thời gian, nhất là trên điện thoại.

### 2.4. Lịch sử

**Ưu điểm**

- So sánh **12 tháng trọn vẹn gần nhất** với mức trung bình của **10 năm trước**, dùng cùng các tháng để giảm lệch do mùa. Hai khoảng thời gian được ghi rõ trên màn hình.
- Biểu đồ cột đôi cho thấy tháng nào mưa cao hoặc thấp hơn mức thường thấy. Thẻ tóm tắt cho biết tổng lượng mưa, tỷ lệ chênh lệch, tháng mưa nhiều nhất và các tháng có nhiệt độ trung bình cao/thấp nhất.
- Nêu rõ nguồn dữ liệu tái phân tích ERA5, ngưỡng “ngày có mưa” từ 1 mm, và có trạng thái tải/lỗi/thử lại.

**Nhược điểm**

- Khoảng thời gian đang cố định: chưa chọn năm hoặc giai đoạn riêng, chưa bấm một tháng để xem chênh lệch và số liệu chi tiết của tháng đó.
- Dữ liệu ERA5 là **tái phân tích theo ô lưới**, không phải phép đo trực tiếp tại mọi địa điểm. Địa hình và thời tiết rất cục bộ có thể khác số hiển thị; biểu đồ hiện chưa thể hiện biên độ biến động giữa các năm của mốc 10 năm.
- Giá trị cụ thể của cột nằm trong tooltip `title`, khó tiếp cận trên màn hình cảm ứng và khi dùng bàn phím. Số tổng và tỷ lệ cũng được tính từ lượng mưa tháng đã làm tròn, nên có thể lệch nhẹ so với phép tính trên số gốc.

Các nhận xét về cách tính và giới hạn hiện tại được đối chiếu từ [nghiệp vụ dự báo](backend/weather_analysis/services/forecast_service.py), [công thức chấm điểm](backend/weather_analysis/services/scoring.py), [nghiệp vụ khí hậu](backend/weather_analysis/services/climate_service.py) và bốn trang trong [`frontend/src/pages`](frontend/src/pages). Thông tin về ERA5 tham khảo [tài liệu Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api).

## 3. Ứng dụng giải quyết vấn đề gì cho người dùng?

| Vấn đề người dùng gặp phải | Chức năng hỗ trợ | Kết quả người dùng nhận được |
|---|---|---|
| Khó quyết định có nên ra ngoài hôm nay và cần chú ý yếu tố nào. | **Tổng quan** tổng hợp dữ liệu hiện tại, điểm theo giờ, nhận định và dự báo bảy ngày. | Nắm tình hình nhanh và biết những khoảng giờ, yếu tố thời tiết cần lưu ý. |
| Muốn chọn giờ cho một hoạt động cụ thể thay vì chỉ xem dự báo chung. | **Khung giờ tốt** chấm điểm theo bốn hoạt động và gợi ý khoảng giờ. | Có điểm khởi đầu để sắp xếp chạy bộ, chụp ảnh, ngồi ngoài trời hoặc phơi quần áo. |
| Phân vân giữa hai điểm đến hoặc chưa biết tháng nào thường thuận lợi. | **So sánh** đặt hai địa điểm cạnh nhau theo tháng và theo dữ liệu khí hậu 10 năm. | Thấy sự khác nhau về nhiệt độ, lượng mưa, số ngày mưa và mùa tương đối phù hợp. |
| Không biết 12 tháng gần đây mưa nhiều hay ít so với thông lệ. | **Lịch sử** đối chiếu từng tháng và tổng cả giai đoạn với mức trung bình 10 năm trước. | Nhận ra mức chênh lệch, tháng mưa nhiều nhất và bối cảnh khí hậu của địa điểm. |
| Thường xuyên theo dõi nhiều địa điểm. | Tìm kiếm địa điểm và lưu mục yêu thích ở thanh chung. | Chuyển địa điểm nhanh hơn khi dùng lại ứng dụng. |

**Giới hạn sử dụng:** các kết quả hỗ trợ tham khảo và lập kế hoạch. Ứng dụng hiện chưa cung cấp cảnh báo thiên tai, dự báo chính xác cho chuyến đi xa trong tương lai hoặc kết luận về nguyên nhân gây ra biến động khí hậu.
