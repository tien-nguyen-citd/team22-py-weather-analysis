# Thử nghiệm chatbot thời tiết

Project thử nghiệm các cách dùng ML để đọc câu hỏi tiếng Việt về thời tiết và rút ra
3 thông tin cần cho phân tích: **thời gian**, **địa điểm** và **loại hoạt động**.

Ví dụ với câu "Mùa này đi Phú Quốc có hợp không?":

- Địa điểm: `phu-quoc`
- Thời gian: `months`, từ 01/09 đến 30/11 (tháng hiện tại và 2 tháng tiếp theo)
- Hoạt động: `travel`

Project này độc lập với `backend`: có môi trường Python và thư viện riêng. Cài đặt
và chạy `weather_analysis` không cần tới project này. Hai bên chỉ dùng chung tệp
địa điểm mẫu `backend/data/seed/locations.csv` và `location-aliases.csv`.

## Cài đặt

```powershell
cd chatbot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Thư viện chiếm khoảng 1GB, phần lớn là PyTorch. Model được tải về thư mục
`chatbot/.models` ở lần chạy đầu tiên của từng cấu hình; tải hết mọi cấu hình cần
khoảng 3GB. Xóa thư mục này để giải phóng ổ cứng, lần chạy sau sẽ tải lại.

## Chạy kiểm tra

```powershell
cd chatbot
.\.venv\Scripts\Activate.ps1
pyright
ruff check .
pytest -q
```

`pytest -q` chỉ chạy các test không cần model. Sau khi đã tải model, kiểm tra độ
chính xác của các cấu hình ML bằng:

```powershell
pytest -m model
```

## Đánh giá các cấu hình

Đánh giá một cấu hình và in các câu trả lời sai:

```powershell
python -m weather_chatbot.evaluate --extractor gliner-multi --show-errors
```

Đánh giá nhiều cấu hình rồi in chung một bảng, mỗi cấu hình chạy trong một process
riêng để đo RAM không bị lẫn nhau:

```powershell
python -m weather_chatbot.evaluate --extractor rule model2vec
```

Đánh giá lần lượt mọi cấu hình:

```powershell
python -m weather_chatbot.evaluate --all
```

`--show-errors` chỉ dùng được khi đánh giá một cấu hình.

`qwen-0.5b` cần vài giây cho mỗi câu hỏi trên CPU nên lệnh `--all` mất khoảng 15 phút.

Các cột trong bảng kết quả:

- `Địa điểm`, `Thời gian`, `Hoạt động`: tỷ lệ câu đúng từng thông tin.
- `Đủ 3`: tỷ lệ câu đúng cả 3 thông tin, tách riêng theo nhóm câu hỏi `basic` và `paraphrase`.
- `Địa điểm lạ`: tỷ lệ nhận ra địa điểm không có trong danh sách (ví dụ Côn Đảo) mà không gán nhầm sang địa điểm khác.
- `Load`: thời gian nạp model. `TB`, `p95`: thời gian xử lý một câu hỏi.
- `RAM`: RAM cao nhất của process. `Model`: dung lượng file model.

| Cấu hình | Cách làm |
| --- | --- |
| `rule` | Không dùng ML. Địa điểm dùng từ điển, thời gian dùng luật, hoạt động dùng từ khóa. |
| `model2vec` | Embedding tĩnh `minishlab/potion-multilingual-128M` nhận diện hoạt động bằng cách tìm câu ví dụ giống nhất. Địa điểm và thời gian dùng luật. |
| `minilm` | Như `model2vec` nhưng dùng `paraphrase-multilingual-MiniLM-L12-v2` chạy qua ONNX Runtime. |
| `rule+model2vec` | Dùng từ khóa trước, chỉ dùng `model2vec` khi câu hỏi không chứa từ khóa nào. |
| `rule+minilm` | Như `rule+model2vec` nhưng dùng `minilm`. |
| `gliner-x-small` | Zero-shot NER `knowledgator/gliner-x-small` (ONNX quantized) tìm cụm địa điểm, thời gian, hoạt động. |
| `gliner-multi` | Zero-shot NER `urchade/gliner_multi-v2.1` chạy bằng PyTorch. |
| `qwen-0.5b` | Mô hình ngôn ngữ `Qwen2.5-0.5B-Instruct` trả về JSON gồm 3 thông tin. |

Với mọi cấu hình, cụm từ tìm được đều qua cùng một bộ chuẩn hóa để thành slug địa
điểm, khoảng thời gian và mã hoạt động.

## Dữ liệu

- `data/questions.csv`: bộ câu hỏi có nhãn dùng để đánh giá.
  - Nhóm `basic`: cách hỏi thông thường, có cả câu không dấu, viết tắt và địa điểm ngoài danh sách.
  - Nhóm `paraphrase`: cách nói tự nhiên, ít dùng từ khóa quen thuộc (ví dụ "lên xe hoa", "hong đồ", "đảo ngọc").
  - Nhãn thời gian được tính theo ngày tham chiếu 16/09/2026 (thứ Tư).
- `data/activities.csv`: danh mục hoạt động và từ khóa cho cách làm bằng luật.
- `data/activity-examples.csv`: câu ví dụ cho các cấu hình embedding. Để kết quả đánh giá khách quan, không chép câu trong `questions.csv` sang đây.

Để trống `activity_id` nghĩa là câu hỏi thời tiết chung, không nói tới hoạt động nào.

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
| `best_time` | tháng mấy, khi nào, mùa nào, ngày nào | Nếu câu có thêm khoảng thời gian (ví dụ "tuần sau ngày nào") thì đó là phạm vi tìm |

Khi câu hỏi có nhiều cụm thời gian, thứ tự ưu tiên là: hỏi thời điểm tốt nhất, rồi
khoảng thời gian cụ thể, rồi hiện tại.

## Cấu trúc chính

- `weather_chatbot/question_info.py`: kết quả chung `QuestionInfo`, `TimeSlot`, `TimeKind`.
- `weather_chatbot/text.py`: tách từ, bỏ dấu và tìm cụm từ trong câu, hiểu cả câu gõ không dấu.
- `weather_chatbot/locations.py`, `time_parser.py`, `activities.py`: bộ chuẩn hóa địa điểm, thời gian, hoạt động.
- `weather_chatbot/extractors/`: các cách trích xuất, cùng tuân theo `QuestionExtractor`.
- `weather_chatbot/models.py`: tải model vào `chatbot/.models` và đo dung lượng.
- `weather_chatbot/evaluation.py`, `evaluate.py`: chấm điểm và lệnh đánh giá.
- `tests/`: unit test và test độ chính xác của model.
