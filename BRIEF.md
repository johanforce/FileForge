# FileForge — Product Brief

## 1. Mục tiêu sản phẩm

FileForge là ứng dụng desktop chạy cục bộ trên macOS, Windows và Linux. Mục tiêu là gom các thao tác xử lý tệp thường dùng vào một giao diện gọn, trực quan, ưu tiên hành động thay vì nội dung mô tả dài.

## 2. Nguyên tắc UX

- Giao diện tiếng Việt, dark theme, ưu tiên vùng thao tác chính.
- Hạn chế text view và các bảng thống kê không cần thiết.
- Các tác vụ chạy nền khi có thể; giao diện không bị khóa trong lúc xử lý.
- Có phản hồi tiến trình, lỗi rõ ràng và đường dẫn kết quả.
- Tệp được xử lý tại máy người dùng, không tải lên máy chủ.

## 3. Các khu vực chức năng

### 3.1 Nén ZIP

- Thêm nhiều tệp hoặc thư mục; hỗ trợ kéo thả.
- Chọn mức nén nhanh nhất, cân bằng hoặc nén tối đa.
- Giữ cấu trúc thư mục tương đối trong ZIP.
- Chạy nền và hiển thị tiến trình.

### 3.2 Giải nén ZIP

- Giải nén nhiều ZIP trong một lượt.
- Mỗi ZIP được giải nén vào thư mục riêng, tránh ghi đè do trùng tên.
- Từ chối đường dẫn tuyệt đối, path traversal và symbolic link.
- Báo lỗi riêng theo từng archive và tiếp tục xử lý các archive hợp lệ.

### 3.3 Chuyển đổi ảnh

- Đầu vào: PNG, JPG/JPEG, WEBP, BMP, TIFF.
- Đầu ra: JPG, PNG, WEBP.
- Có điều chỉnh chất lượng cho JPG/WEBP.
- Xoay ảnh theo EXIF; giữ ICC profile khi có thể.
- Khi chuyển ảnh có alpha sang JPG, ghép trên nền trắng.
- Không ghi đè đầu ra đã có; tự thêm hậu tố tên tệp.

### 3.4 Công cụ JSON / XML

Tab riêng tên JSON / XML, có hai vùng đầu vào và kết quả.

Chức năng:
- JSON → Chuỗi: parse JSON rồi serialize dạng compact, không indent.
- Chuỗi → JSON: parse JSON text rồi hiển thị JSON có indent 2 spaces.
- Định dạng JSON: parse và pretty-print, giữ Unicode.
- XML → Chuỗi: parse XML hợp lệ rồi serialize compact.
- Chuỗi → XML: nhận XML raw hoặc JSON string chứa XML, parse và pretty-print.
- JSON → Model: sinh khai báo model cho Python dataclass, Pydantic v2 hoặc TypeScript interface.

Model generator:
- Nhận object, array hoặc scalar ở root; array/scalar được bọc trong field root.
- Sinh các model riêng cho object lồng nhau và object trong array.
- Suy luận string, integer, float, boolean, null, list và object.
- Hợp nhất object mẫu trong array; trường không xuất hiện ở mọi phần tử được đánh dấu optional.
- Với Python, xử lý khóa không hợp lệ bằng identifier an toàn; Pydantic dùng alias khi tên khóa khác identifier.

Trình xem JSON:
- Cả đầu vào và đầu ra JSON có chế độ Văn bản và Cấu trúc.
- Cấu trúc dùng cây hai cột: tên trường và giá trị.
- Object/array có thể bung/thu từng cấp.
- Nạp node con theo yêu cầu; tối đa 300 mục hiển thị mỗi node để giảm tải UI.

## 4. Hiệu năng và xử lý nền

- Parse/serialize JSON, parse/format XML và sinh model phải chạy trong QThread.
- Text editor dùng QPlainTextEdit thay vì widget rich-text nặng.
- Cây JSON lazy-load; không dựng toàn bộ widget con ngay khi parse.
- Yêu cầu trải nghiệm: xử lý chuỗi JSON khoảng 10.000 ký tự mà không làm cửa sổ đứng hoặc mất phản hồi.
- Bộ kiểm thử có ca dữ liệu 10.000 ký tự; cần tiếp tục kiểm tra thực tế trên macOS với dữ liệu lồng nhau lớn.

## 5. Xử lý lỗi và tính toàn vẹn

- JSON/XML không hợp lệ phải báo lỗi thân thiện, giữ nguyên dữ liệu đầu vào.
- File hỏng trong batch không làm dừng các file hợp lệ còn lại (trừ lỗi nghiêm trọng của toàn tác vụ).
- Tác vụ ghi file ưu tiên ghi ra file tạm rồi thay thế/commit kết quả khi hoàn tất.
- Giải nén kiểm tra đường dẫn từng member trước khi ghi ra đĩa.

## 6. Trạng thái triển khai

- Nén ZIP: đã có.
- Giải nén ZIP: đã có.
- Chuyển đổi ảnh: đã có.
- JSON/XML conversions: đang được triển khai trong tab JSON / XML.
- JSON → Model: đang được triển khai, hỗ trợ dataclass, Pydantic v2 và TypeScript.
- Đóng gói .app/.dmg cho macOS: chưa triển khai.

## 7. Ngoài phạm vi hiện tại

- Convert PDF/Word/Excel.
- Đồng bộ cloud hoặc upload file.
- JSON Schema validation và OpenAPI generation.
- Benchmark cam kết cho dữ liệu lớn hơn 10.000 ký tự; hiệu năng còn phụ thuộc độ sâu và số lượng node.