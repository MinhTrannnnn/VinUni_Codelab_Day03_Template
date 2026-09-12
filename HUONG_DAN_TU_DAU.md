# Học từ đầu: Chatbot, Tool Calling và ReAct Agent

Tài liệu này giải thích bài Lab Day 03 theo thứ tự dành cho người mới:

1. Hiểu vấn đề cần giải quyết.
2. Học các khái niệm bằng ví dụ đời thường.
3. Quan sát một yêu cầu được xử lý từ đầu đến cuối.
4. Sau cùng mới đọc và giải thích code trong repository.

## Mục lục học nhanh

- Phần 1–3: Chatbot, LLM và hallucination.
- Phần 4–6: Tool, JSON và Tool Registry.
- Phần 7–11: Agent, ReAct, iteration, trace và safeguard.
- Phần 12: Ví dụ hoàn chỉnh từ câu hỏi đến câu trả lời.
- Phần 13–17: Giải thích code trong repository.
- Phần 18–20: Khả năng, giới hạn và các bảng so sánh.
- Phần 21–23: Cách chạy, câu hỏi tự kiểm tra và bài tập mở rộng.

---

## 1. Bài toán của chúng ta

Người dùng hỏi:

> Tìm cho tôi chuyến bay từ HAN đi SGN dưới 2 triệu, rồi cho biết thời tiết SGN nên mặc gì?

Để trả lời chính xác, chương trình phải làm nhiều việc:

1. Hiểu `HAN` là điểm đi và `SGN` là điểm đến.
2. Hiểu ngân sách tối đa là 2.000.000 VND.
3. Tìm dữ liệu chuyến bay phù hợp.
4. Tìm dữ liệu thời tiết tại SGN.
5. Tổng hợp hai kết quả thành một câu trả lời dễ đọc.

Một mô hình chỉ biết tạo văn bản không tự động có dữ liệu chuyến bay và thời tiết. Vì vậy, bài lab giới thiệu **tool** và **agent**.

---

## 2. Chatbot là gì?

Chatbot là chương trình nhận tin nhắn của người dùng và trả về tin nhắn phản hồi.

Luồng đơn giản nhất:

```text
Người dùng → Chatbot → Câu trả lời
```

Ví dụ:

```text
Người dùng: Xin chào!
Chatbot: Chào bạn, tôi có thể giúp gì?
```

Chatbot không nhất thiết phải dùng AI. Một chatbot rất đơn giản có thể dùng `if/else`:

```python
if user_input == "Xin chào":
    answer = "Chào bạn!"
else:
    answer = "Tôi chưa hiểu câu hỏi."
```

### Chatbot theo luật

Chatbot theo luật tìm từ khóa hoặc so sánh câu hỏi với những mẫu có sẵn.

Ưu điểm:

- Dễ viết.
- Kết quả ổn định.
- Dễ kiểm thử.
- Không tốn chi phí gọi mô hình AI.

Nhược điểm:

- Chỉ hiểu những trường hợp người lập trình đã dự đoán.
- Khó xử lý ngôn ngữ linh hoạt.
- Càng nhiều luật thì code càng phức tạp.

### Chatbot dùng LLM

LLM là viết tắt của **Large Language Model**, tức mô hình ngôn ngữ lớn. Ví dụ có GPT hoặc Gemini.

Một LLM được huấn luyện để dự đoán và tạo văn bản. Nó có thể:

- Hiểu nhiều cách diễn đạt.
- Giải thích kiến thức.
- Tóm tắt và viết nội dung.
- Trò chuyện tự nhiên hơn chatbot theo luật.

Tuy nhiên, bản thân LLM không mặc nhiên biết dữ liệu đang thay đổi như:

- Giá vé hiện tại.
- Ghế còn trống.
- Thời tiết lúc này.
- Số dư tài khoản.
- Trạng thái đơn hàng.

---

## 3. Hallucination là gì?

Hallucination xảy ra khi mô hình tạo ra thông tin nghe hợp lý nhưng không được xác nhận bởi dữ liệu đáng tin cậy.

Ví dụ chatbot không có dữ liệu nhưng trả lời:

```text
Chuyến VN999 khởi hành lúc 10:00, giá 1.200.000 VND.
```

Nếu chuyến `VN999` không tồn tại, câu trả lời đó là thông tin bịa đặt.

Một cách trả lời an toàn hơn là:

```text
Tôi chưa được kết nối với hệ thống chuyến bay nên không thể xác nhận giá và lịch bay.
```

`ChatbotBaseline` trong bài có vai trò minh họa giới hạn này.

---

## 4. Tool là gì?

Tool là một hàm mà chatbot hoặc agent được phép gọi để lấy dữ liệu hay thực hiện một tác vụ.

Hãy tưởng tượng một nhân viên tư vấn du lịch:

- Bộ não của nhân viên dùng để hiểu yêu cầu.
- Phần mềm đặt vé là công cụ tìm chuyến bay.
- Ứng dụng thời tiết là công cụ xem thời tiết.

Nhân viên không cần ghi nhớ toàn bộ lịch bay. Họ biết khi nào cần mở đúng công cụ.

Trong bài lab có hai tool:

```python
get_flight_info(origin, destination, max_price)
get_weather_forecast(city_code)
```

Ví dụ gọi tool chuyến bay:

```python
flights = get_flight_info(
    origin="HAN",
    destination="SGN",
    max_price=2_000_000,
)
```

Ví dụ gọi tool thời tiết:

```python
weather = get_weather_forecast(city_code="SGN")
```

Trong lab, hai tool đọc file JSON cục bộ. Chúng **không gọi Internet** và không cung cấp dữ liệu thời gian thực.

---

## 5. JSON là gì?

JSON là cách biểu diễn dữ liệu bằng cặp `key: value`.

Ví dụ một chuyến bay:

```json
{
  "flight_number": "VN213",
  "origin": "HAN",
  "destination": "SGN",
  "price_vnd": 1850000
}
```

Trong Python, dữ liệu tương ứng thường là một `dict`:

```python
flight = {
    "flight_number": "VN213",
    "origin": "HAN",
    "destination": "SGN",
    "price_vnd": 1_850_000,
}
```

Action của agent cũng được biểu diễn bằng cấu trúc tương tự JSON:

```json
{
  "name": "get_flight_info",
  "args": {
    "origin": "HAN",
    "destination": "SGN",
    "max_price": 2000000
  }
}
```

Trong đó:

- `name`: tên tool muốn gọi.
- `args`: các tham số truyền cho tool.

---

## 6. Tool Registry là gì?

Tool Registry là danh bạ các công cụ mà agent được phép sử dụng.

Ví dụ danh bạ điện thoại:

```text
"Mẹ" → số điện thoại của mẹ
"Bạn An" → số điện thoại của An
```

Tool Registry hoạt động tương tự:

```python
TOOL_MAP = {
    "get_flight_info": get_flight_info,
    "get_weather_forecast": get_weather_forecast,
}
```

Khi agent chọn tên `get_flight_info`, chương trình lấy đúng hàm Python:

```python
tool = TOOL_MAP["get_flight_info"]
```

Sau đó gọi hàm với các tham số:

```python
observation = tool(**args)
```

Nếu `args` là:

```python
{
    "origin": "HAN",
    "destination": "SGN",
    "max_price": 2_000_000,
}
```

thì `tool(**args)` tương đương với:

```python
tool(
    origin="HAN",
    destination="SGN",
    max_price=2_000_000,
)
```

Registry giúp ta thêm tool mới mà không phải viết lại toàn bộ agent.

---

## 7. Agent là gì?

Một chatbot thông thường chủ yếu tạo câu trả lời. Một agent có thêm khả năng:

1. Xác định mục tiêu.
2. Chọn hành động.
3. Sử dụng công cụ.
4. Quan sát kết quả.
5. Quyết định bước tiếp theo.

Luồng đơn giản:

```text
Người dùng
    ↓
Hiểu yêu cầu
    ↓
Chọn công cụ
    ↓
Gọi công cụ
    ↓
Đọc kết quả
    ↓
Trả lời hoặc tiếp tục hành động
```

Agent không nhất thiết phải dùng LLM. Nó có thể lập kế hoạch bằng luật Python. Agent trong bài mình làm là dạng này.

---

## 8. ReAct là gì?

ReAct là viết tắt của:

```text
Reasoning + Acting
```

Ý tưởng là kết hợp suy luận với hành động:

```text
Thought → Action → Observation → Thought tiếp theo
```

### Thought

Mô tả ngắn về việc cần làm tiếp theo:

```text
Cần tìm chuyến bay từ HAN đi SGN dưới 2 triệu.
```

Trong lab, `thought` là bản ghi giải thích cấp cao để theo dõi chương trình, không phải toàn bộ suy luận bí mật của một LLM.

### Action

Hành động mà agent chọn:

```python
{
    "name": "get_flight_info",
    "args": {
        "origin": "HAN",
        "destination": "SGN",
        "max_price": 2_000_000,
    },
}
```

### Observation

Kết quả của tool:

```python
[
    {"flight_number": "VN213", "price_vnd": 1_850_000},
    {"flight_number": "VJ151", "price_vnd": 1_450_000},
]
```

### Final Answer

Khi đã đủ dữ liệu, agent tổng hợp câu trả lời cuối cùng:

```text
Có hai chuyến phù hợp: VN213 và VJ151.
SGN hiện 32°C và có mưa; nên mang ô và mặc đồ thoáng mát.
```

---

## 9. Iteration và ReAct Loop

Mỗi vòng xử lý được gọi là một **iteration**.

Yêu cầu chỉ hỏi thời tiết có thể hoàn thành trong một iteration:

```text
Iteration 1: gọi tool thời tiết và trả lời
```

Yêu cầu chuyến bay kết hợp thời tiết cần nhiều iteration:

```text
Iteration 1: tìm chuyến bay
Iteration 2: xem thời tiết
Iteration 3: tổng hợp câu trả lời
```

Một ReAct loop tổng quát có dạng:

```python
iteration = 1

while iteration <= max_iterations:
    result, is_final = plan_and_execute_step(user_input, iteration)

    if is_final:
        return result

    iteration += 1
```

---

## 10. Trace là gì?

Trace là nhật ký các bước agent đã thực hiện.

Ví dụ:

```python
trace = [
    {
        "iteration": 1,
        "thought": "Cần tìm chuyến bay.",
        "action": {"name": "get_flight_info", "args": {...}},
        "observation": [...],
    },
    {
        "iteration": 2,
        "thought": "Cần xem thời tiết.",
        "action": {"name": "get_weather_forecast", "args": {...}},
        "observation": {...},
    },
]
```

Trace giúp:

- Tìm lỗi khi agent trả lời sai.
- Biết agent đã gọi tool nào.
- Kiểm tra tham số truyền vào tool.
- Xem dữ liệu tool trả về.
- Đánh giá agent chạy bao nhiêu bước.

Nếu không có trace, ta chỉ thấy câu trả lời cuối và khó biết lỗi xảy ra ở đâu.

---

## 11. Safeguard là gì?

Safeguard là biện pháp bảo vệ hệ thống khỏi hành vi không mong muốn.

Ví dụ tool trả lỗi, nhưng agent cứ gọi lại vô hạn:

```text
Gọi tool → lỗi → gọi lại → lỗi → gọi lại → ...
```

Ta giới hạn số vòng lặp:

```python
max_iterations = 5
```

Khi hết số bước cho phép, agent trả về:

```python
{
    "status": "max_iterations_reached",
    "answer": "Không thể hoàn thành trong số bước tối đa.",
}
```

Agent thật còn có thể cần:

- Timeout.
- Giới hạn chi phí API.
- Giới hạn số lần gọi một tool.
- Xác nhận của người dùng trước hành động quan trọng.
- Chống thực hiện trùng một hành động.

---

## 12. Theo dõi một câu hỏi từ đầu đến cuối

Câu hỏi:

```text
Tìm cho tôi chuyến bay từ HAN đi SGN dưới 2 triệu,
rồi cho biết thời tiết SGN nên mặc gì?
```

### Bước 1: Nhận diện ý định

Chương trình thấy:

- Có cụm `chuyến bay` nên cần tool chuyến bay.
- Có cụm `thời tiết` và `mặc gì` nên cần tool thời tiết.

Kết quả:

```python
needs_flight = True
needs_weather = True
```

### Bước 2: Tách thông tin

```python
origin = "HAN"
destination = "SGN"
max_price = 2_000_000
```

### Bước 3: Gọi tool chuyến bay

```python
get_flight_info("HAN", "SGN", 2_000_000)
```

Tool tìm được `VN213` và `VJ151`.

### Bước 4: Gọi tool thời tiết

```python
get_weather_forecast("SGN")
```

Tool trả về TP. Hồ Chí Minh, 32°C, có mưa và gợi ý trang phục.

### Bước 5: Tổng hợp

Agent ghép dữ liệu từ hai tool thành câu trả lời cuối cùng. Nó không tự đoán số hiệu chuyến bay hoặc nhiệt độ.

---

# Phần II: Giải thích code trong repository

## 13. Cấu trúc dự án

```text
VinUni_Codelab_Day03_Template/
├── autograder/
│   └── test_agent.py
├── raw-data/
│   ├── customer_queries.json
│   ├── flight_data.json
│   └── weather_data.json
├── starter-code/
│   ├── README.md
│   ├── requirements.txt
│   ├── template.py
│   └── tools.py
└── student_guide.md
```

Vai trò từng phần:

- `raw-data/`: dữ liệu giả lập của lab.
- `tools.py`: định nghĩa các công cụ.
- `template.py`: chứa chatbot baseline và ReAct Agent.
- `test_agent.py`: kiểm tra code có hoạt động đúng không.
- `student_guide.md`: hướng dẫn ngắn của ban tổ chức.

---

## 14. Giải thích `tools.py`

### Xác định thư mục dữ liệu

```python
RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "raw-data")
```

- `__file__` là đường dẫn file `tools.py`.
- `os.path.dirname(__file__)` lấy thư mục `starter-code`.
- `..` đi lên thư mục gốc.
- `raw-data` đi vào thư mục dữ liệu.

Nhờ đó, chương trình vẫn tìm đúng dữ liệu dù được chạy từ thư mục làm việc khác.

### Tool chuyến bay

```python
def get_flight_info(origin, destination, max_price=5_000_000):
```

Hàm này:

1. Mở `flight_data.json`.
2. Chuyển JSON thành list Python.
3. Duyệt từng chuyến bay.
4. Chỉ giữ chuyến đúng điểm đi, điểm đến và ngân sách.

Điều kiện lọc chính:

```python
fl["origin"].upper() == origin.upper()
and fl["destination"].upper() == destination.upper()
and fl["price_vnd"] <= max_price
```

`.upper()` giúp `han` và `HAN` được xem như nhau.

### Tool thời tiết

```python
def get_weather_forecast(city_code):
```

Hàm đọc `weather_data.json`, sau đó lấy dữ liệu theo mã thành phố:

```python
weather_data.get(city_code.upper(), default_error)
```

Dùng `.get()` giúp tránh `KeyError`. Nếu thành phố không tồn tại, hàm trả một object chứa `error`.

### TOOL_DEFINITIONS và TOOL_MAP

`TOOL_DEFINITIONS` mô tả cho agent biết:

- Tên tool.
- Mục đích của tool.
- Các tham số cần truyền.

`TOOL_MAP` chứa hàm Python thật để chương trình thực thi.

Có thể hiểu:

```text
TOOL_DEFINITIONS = tài liệu hướng dẫn dùng tool
TOOL_MAP         = danh bạ trỏ đến code của tool
```

---

## 15. Giải thích `ChatbotBaseline`

Code hiện tại:

```python
class ChatbotBaseline:
    def query(self, user_input):
        return {
            "status": "success",
            "answer": "Tôi chưa thể tra cứu dữ liệu...",
            "tool_calls": [],
        }
```

Kết quả là dictionary vì autograder cần kiểm tra từng thuộc tính.

### `status`

```python
"status": "success"
```

Nghĩa là chatbot đã xử lý request thành công. Nó không có nghĩa dữ liệu chuyến bay đã được tìm thấy.

### `answer`

Là câu trả lời hiển thị cho người dùng.

### `tool_calls`

```python
"tool_calls": []
```

Danh sách rỗng chứng minh baseline không sử dụng công cụ.

---

## 16. Các hàm hỗ trợ trong `ReActAgent`

### `_airport_codes()`

Hàm này tìm mã sân bay bằng regular expression:

```python
re.findall(r"\b[A-Za-z]{3}\b", user_input)
```

Nó tìm các từ có đúng ba chữ cái. Sau đó chỉ giữ mã hợp lệ:

```python
{"HAN", "SGN", "DAD"}
```

Hàm cũng ánh xạ tên thành phố:

```python
"hà nội" → "HAN"
"sài gòn" → "SGN"
"đà nẵng" → "DAD"
```

Vì vậy hai câu sau đều được hiểu:

```text
Thời tiết DAD thế nào?
Thời tiết Đà Nẵng thế nào?
```

### `_max_price()`

Hàm dùng regex để hiểu ngân sách:

```text
2 triệu   → 2.000.000
1.5 triệu → 1.500.000
1,5 triệu → 1.500.000
500k      → 500.000
```

Nếu người dùng không ghi ngân sách, chương trình dùng mặc định:

```python
5_000_000
```

### `_execute_action()`

Đây là cổng thực thi tool.

Nếu Action là chuỗi JSON, chương trình parse:

```python
action = json.loads(action)
```

Nếu JSON sai:

```python
{"error": "Invalid JSON format"}
```

Tên tool được chuẩn hóa:

```python
tool_name = str(action.get("name", "")).strip().lower()
```

Ví dụ:

```text
" Get_Flight_Info " → "get_flight_info"
```

Sau đó chương trình tìm tool an toàn:

```python
tool = TOOL_MAP.get(tool_name)
```

Nếu không có tool, chương trình trả lỗi thay vì crash.

### `_format_flights()` và `_format_weather()`

Tool trả về dữ liệu Python. Hai hàm này chuyển dữ liệu thành văn bản thân thiện với người dùng.

### `_result()`

Hàm thống nhất cấu trúc kết quả:

```python
{
    "status": status,
    "answer": answer,
    "iterations": len(self.trace),
    "trace": self.trace.copy(),
}
```

---

## 17. Giải thích `ReActAgent.run()`

### Làm sạch trace cũ

```python
self.trace = []
```

Nếu cùng một object agent được gọi nhiều lần, kết quả cũ không được lẫn vào lần chạy mới.

### Kiểm tra giới hạn

```python
if self.max_iterations <= 0:
```

Nếu không được phép chạy bước nào, agent trả trạng thái `max_iterations_reached` ngay.

### Nhận diện FAQ

```python
is_faq = any(
    term in lowered
    for term in ("chính sách", "đổi trả", "đổi vé", "hoàn vé")
)
```

FAQ được kiểm tra trước yêu cầu chuyến bay. Điều này rất quan trọng với câu:

```text
Chính sách đổi trả vé máy bay Vinpearl như thế nào?
```

Câu có chữ `vé máy bay`, nhưng người dùng không muốn tìm chuyến. Họ hỏi chính sách.

### Nhận diện nhu cầu dùng tool

```python
needs_flight = ...
needs_weather = ...
```

Nếu `needs_flight` là `True`, agent chuẩn bị Action chuyến bay. Nếu `needs_weather` là `True`, agent chuẩn bị Action thời tiết.

### Chạy tool chuyến bay

Agent tạo Action:

```python
action = {
    "name": "get_flight_info",
    "args": {
        "origin": origin,
        "destination": destination,
        "max_price": max_price,
    },
}
```

Sau đó:

```python
observation = self._execute_action(action)
```

Và ghi trace:

```python
self.trace.append({
    "iteration": 1,
    "thought": "...",
    "action": action,
    "observation": observation,
})
```

### Chạy tool thời tiết

Quá trình tương tự nhưng Action là:

```python
{
    "name": "get_weather_forecast",
    "args": {"city_code": city_code},
}
```

### Tổng hợp yêu cầu nhiều bước

Nếu câu hỏi cần cả hai tool, agent thêm bước cuối để biểu diễn việc đã đủ dữ liệu:

```python
{
    "thought": "Đã có đủ dữ liệu để tổng hợp câu trả lời cuối cùng.",
    "action": None,
    "observation": "Final answer ready",
}
```

### FAQ không gọi tool

Nếu không cần chuyến bay hoặc thời tiết, agent trả hướng dẫn chung và lưu:

```python
"action": None
```

Điều này chứng minh agent không phải lúc nào cũng phải dùng tool. Một agent tốt chỉ dùng tool khi cần.

---

## 18. Chatbot này thực sự làm được gì?

Phần đã xây dựng gồm hai chế độ.

### Baseline chatbot làm được

- Nhận câu hỏi.
- Trả một câu trả lời an toàn.
- Không gọi tool.

Baseline không thực sự hiểu và tra cứu yêu cầu.

### ReAct Agent làm được

- Phân biệt câu hỏi chuyến bay, thời tiết và FAQ.
- Hiểu các mã `HAN`, `SGN`, `DAD`.
- Hiểu một số tên thành phố tương ứng.
- Hiểu ngân sách viết theo `triệu` hoặc `k`.
- Tìm chuyến bay trong dữ liệu JSON.
- Lấy thời tiết từ dữ liệu JSON.
- Xử lý câu hỏi cần hai tool.
- Thông báo khi không có chuyến phù hợp.
- Ghi trace từng bước.
- Dừng khi đạt giới hạn iteration.

### ReAct Agent chưa làm được

- Không dùng Gemini, GPT hoặc LLM khác.
- Không truy cập Internet.
- Không lấy chuyến bay và thời tiết theo thời gian thực.
- Không đặt hoặc thanh toán vé.
- Không hiểu mọi thành phố trên thế giới.
- Không trả lời tốt mọi câu hỏi tự do.
- Không tự phát hiện hay tạo tool mới.

Tên gọi chính xác nhất của sản phẩm hiện tại là:

> Một chatbot demo có ReAct Agent lập kế hoạch bằng luật Python và sử dụng hai tool đọc dữ liệu local.

---

## 19. So sánh ba cấp độ

| Tiêu chí | Chatbot theo luật | LLM chatbot | ReAct Agent trong lab |
|---|---|---|---|
| Hiểu ngôn ngữ linh hoạt | Thấp | Cao | Trung bình, dựa trên từ khóa |
| Tạo văn bản tự nhiên | Hạn chế | Tốt | Theo mẫu Python |
| Dùng tool | Có thể lập trình thêm | Không mặc định | Có |
| Tra dữ liệu lab | Không | Không mặc định | Có |
| Nguy cơ hallucination | Thấp | Có | Thấp hơn vì dùng dữ liệu tool |
| Xử lý nhiều bước | Khó | Có thể mô tả nhưng chưa hành động | Có |
| Kết quả ổn định | Cao | Có thể thay đổi | Cao |
| Cần API key | Không | Thường có | Không |

### So sánh baseline và agent trong chính bài này

| Nội dung | `ChatbotBaseline` | `ReActAgent` |
|---|---|---|
| Gọi tool | Không | Có |
| Tìm chuyến bay | Không | Có |
| Xem thời tiết | Không | Có |
| Trace | Không | Có |
| Nhiều bước | Không | Có |
| Safeguard vòng lặp | Không cần | Có |
| Nguồn câu trả lời | Văn bản tĩnh | Dữ liệu JSON và logic Python |

---

## 20. So sánh agent trong lab với agent dùng LLM thật

Agent hiện tại:

```text
Câu hỏi
→ Python dò từ khóa
→ Python chọn tool
→ Tool đọc JSON
→ Python định dạng kết quả
```

Agent dùng LLM thật:

```text
Câu hỏi
→ LLM hiểu yêu cầu
→ LLM tạo Action JSON
→ Chương trình xác thực Action
→ Tool được thực thi
→ Observation gửi lại cho LLM
→ LLM quyết định gọi tiếp hay trả lời
```

LLM agent linh hoạt hơn nhưng cũng khó kiểm soát hơn. Nó có thể chọn sai tool, tạo JSON sai, chạy quá nhiều bước và làm tăng chi phí API. Vì vậy những phần như Registry, validation, trace và safeguard trong bài vẫn rất cần thiết khi chuyển sang LLM thật.

---

## 21. Chạy chương trình

Tại thư mục gốc repository:

```bash
source .venv/bin/activate
python starter-code/template.py
```

Chạy autograder:

```bash
python -m pytest autograder/test_agent.py -v
```

Kết quả hiện tại:

```text
8 passed
```

---

## 22. Cách tự kiểm tra xem đã hiểu chưa

Hãy thử trả lời trước khi xem đáp án.

### Câu 1

Vì sao chatbot baseline không nên tự đưa ra giá vé cụ thể?

<details>
<summary>Đáp án</summary>

Vì nó không dùng tool và không có dữ liệu chuyến bay để xác nhận. Giá vé cụ thể có thể là hallucination.

</details>

### Câu 2

`TOOL_MAP` dùng để làm gì?

<details>
<summary>Đáp án</summary>

Nó ánh xạ tên tool trong Action sang hàm Python thật để chương trình có thể thực thi.

</details>

### Câu 3

Khác biệt giữa Action và Observation là gì?

<details>
<summary>Đáp án</summary>

Action mô tả tool cần gọi và tham số. Observation là kết quả nhận được sau khi gọi tool.

</details>

### Câu 4

Vì sao câu hỏi chuyến bay kết hợp thời tiết cần nhiều iteration?

<details>
<summary>Đáp án</summary>

Vì agent phải gọi hai tool độc lập, nhận hai kết quả, rồi tổng hợp thành câu trả lời cuối.

</details>

### Câu 5

Tại sao cần `max_iterations`?

<details>
<summary>Đáp án</summary>

Để tránh agent lặp vô hạn khi tool lỗi hoặc khi agent không thể đi đến câu trả lời cuối.

</details>

### Câu 6

Agent trong lab có phải chatbot AI tổng quát không?

<details>
<summary>Đáp án</summary>

Không. Nó là agent demo chọn hành động bằng luật Python và chỉ dùng hai tool với dữ liệu local.

</details>

---

## 23. Bài tập nhỏ để học sâu hơn

1. Thêm dữ liệu thời tiết cho `HUI` hoặc một mã thành phố mới.
2. Viết tool `get_hotel_info()` và đăng ký vào `TOOL_MAP`.
3. Thêm khả năng hiểu giá `2m` hoặc `2.000.000 đồng`.
4. Thêm test cho câu hỏi thiếu điểm đến.
5. Thêm trường `tool_calls` vào kết quả ReAct Agent để thống kê số tool đã dùng.
6. Sau khi hiểu bản theo luật, thử thay phần nhận diện ý định bằng một LLM thật.

Thứ tự học nên là:

```text
Tool đơn lẻ
→ Tool Registry
→ Action và Observation
→ Trace
→ ReAct nhiều bước
→ Safeguard
→ Cuối cùng mới tích hợp LLM thật
```

Nếu hiểu được chuỗi trên, bạn đã nắm được phần cốt lõi của bài Day 03.
