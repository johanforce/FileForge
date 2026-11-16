# FileForge 1.0.0 — Product Brief

**Phiên bản hiện tại: 1.0.0** · **Ngôn ngữ giao diện:** Tiếng Việt và English.\n\n## 1. Mục tiêu sản phẩm

FileForge là ứng dụng desktop chạy cục bộ trên macOS, Windows và Linux. Mục tiêu là gom các thao tác xử lý tệp thường dùng vào một giao diện gọn, trực quan, ưu tiên hành động thay vì nội dung mô tả dài.

## 2. Nguyên tắc UX

- Giao diện hỗ trợ Tiếng Việt và English, dark theme, ưu tiên vùng thao tác chính. Ngôn ngữ được chọn trong Tùy chọn và lưu giữa các phiên.
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
- Nạp node con theo yêu cầu; hiển thị 300 mục mỗi trang. Có thể nạp tiếp các trang sau, không bỏ mất field nào.

## 4. Hiệu năng và xử lý nền

- Parse/serialize JSON, parse/format XML và sinh model phải chạy trong QThread.
- Text editor dùng QPlainTextEdit thay vì widget rich-text nặng.
- Cây JSON lazy-load; không dựng toàn bộ widget con ngay khi parse.
- Ô nhập không đặt giới hạn số ký tự cố định; dùng QPlainTextEdit với chế độ không tự ngắt dòng để giảm tải cho nội dung một dòng rất dài.
- Parse/format/chuyển đổi chạy trong QThread để không chiếm UI thread.
- Bộ kiểm thử xác nhận nhập và xử lý JSON có chuỗi 150.000 ký tự; đây là mức kiểm thử tối thiểu đã xác nhận, không phải giới hạn tối đa.

## 5. Xử lý lỗi và tính toàn vẹn

- JSON/XML không hợp lệ phải báo lỗi thân thiện, giữ nguyên dữ liệu đầu vào.
- File hỏng trong batch không làm dừng các file hợp lệ còn lại (trừ lỗi nghiêm trọng của toàn tác vụ).
- Tác vụ ghi file ưu tiên ghi ra file tạm rồi thay thế/commit kết quả khi hoàn tất.
- Giải nén kiểm tra đường dẫn từng member trước khi ghi ra đĩa.

## 6. Trải nghiệm desktop và dữ liệu ứng dụng

- Tùy chọn người dùng được lưu bằng QSettings: khôi phục cửa sổ/tab, thư mục gần nhất, thư mục đầu ra ưu tiên và tùy chọn nén/chuyển ảnh.
- Lịch sử tác vụ lưu cục bộ bằng SQLite cho ZIP, giải nén, chuyển ảnh và xử lý JSON/XML; hỗ trợ tìm kiếm, xem chi tiết, mở thư mục kết quả và xóa lịch sử; giới hạn mặc định 500 bản ghi gần nhất.
- Lịch sử chỉ ghi metadata như tên tệp/nhãn đầu vào, số ký tự xử lý, đường dẫn đầu ra, trạng thái và thời lượng. Không lưu nội dung tệp, nội dung editor, khóa AES hay plaintext/ciphertext.
- Nhật ký chẩn đoán dùng RotatingFileHandler, mỗi log tối đa khoảng 2 MB và giữ tối đa 3 bản sao cũ.
- Menu FileForge cho phép mở lịch sử, thư mục cấu hình và thư mục log.
- System tray và thông báo hoàn tất được bật khi môi trường desktop hỗ trợ; người dùng có thể chọn thu nhỏ xuống khay khi đóng cửa sổ.
- Tác vụ ZIP, giải nén và chuyển ảnh hỗ trợ hủy hợp tác qua Event; không ép kết thúc QThread.
- ZIP chỉ thay thế đích sau khi ghi/kiểm tra xong; hủy sẽ xóa tệp tạm và giữ nguyên đầu ra cũ. Giải nén dọn thư mục tạm của archive đang xử lý; ảnh chỉ được publish sau khi ghi xong.
- Nếu batch đã tạo một số kết quả hoàn chỉnh trước khi hủy, các kết quả đó được giữ lại và ghi trong lịch sử với trạng thái `cancelled`.
- Hủy được quan sát giữa các khối dữ liệu ZIP/giải nén và giữa các bước ảnh; một lệnh Pillow đang decode/encode có thể chỉ dừng tại điểm kiểm tra kế tiếp.
- Khi có tác vụ nền đang chạy, yêu cầu thoát ứng dụng được từ chối để tránh hủy QThread đang hoạt động.

## 7. Trạng thái triển khai

- Nén ZIP: đã có.
- Giải nén ZIP: đã có.
- Chuyển đổi ảnh: đã có.
- JSON/XML conversions: đã triển khai trong tab JSON / XML.
- JSON → Model: đã triển khai, hỗ trợ dataclass, Pydantic v2 và TypeScript.
- Đóng gói .app/.dmg cho macOS: chưa triển khai.

## 8. Giấy phép và ghi nhận\n\n- Mã nguồn FileForge được phát hành theo MIT License (`LICENSE`).\n- Giấy phép và thông báo của các dependency được ghi trong `ACKNOWLEDGMENTS.md`; chúng không bị thay thế bởi giấy phép MIT của ứng dụng.\n- Hướng dẫn English: `README.en.md`.\n\n## 9. Ngoài phạm vi hiện tại

- Convert PDF/Word/Excel.
- Đồng bộ cloud hoặc upload file.
- JSON Schema validation và OpenAPI generation.
- Benchmark dung lượng cực lớn ngoài mốc kiểm thử 150.000 ký tự; hiệu năng thực tế còn phụ thuộc cấu trúc lồng nhau, số lượng khóa, bộ nhớ và máy người dùng.