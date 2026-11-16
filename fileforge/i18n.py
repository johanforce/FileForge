"""Lightweight runtime translations for FileForge.

The Vietnamese strings remain the source text. English is an additional UI
catalog; stable item data is kept separate from translated display labels.
"""
from __future__ import annotations

import re
from typing import Any

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractButton,
    QComboBox,
    QDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QTabBar,
    QTabWidget,
    QTableWidget,
    QTextEdit,
    QTreeWidget,
    QWidget,
)

SUPPORTED_LANGUAGES = ("vi", "en")
LANGUAGE_NAMES = {"vi": "Tiếng Việt", "en": "English"}
_current_language = "vi"

ENGLISH = {
    "Trả về ảnh trong thư mục assets/ (pixmap rỗng nếu thiếu file).": "Returns an image from assets/ (an empty pixmap if the file is missing).",
    "Icon nhiều kích thước cho thanh tiêu đề, taskbar và Alt+Tab.": "Multi-size icon for the title bar, taskbar, and Alt+Tab.",
    "Tự vẽ nền trắng + viền bo tròn cho popup, không phụ thuộc stylesheet.": "Draws a white rounded popup without relying on the application stylesheet.",
    "Nhanh nhất": "Fastest",
    "Cân bằng": "Balanced",
    "Nén tối đa": "Maximum compression",
    "Ảnh (*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff)": "Images (*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff)",
    "Tệp ZIP (*.zip)": "ZIP files (*.zip)",
    "Tác vụ không hợp lệ.": "Invalid operation.",
    "TRƯỜNG": "FIELD",
    "GIÁ TRỊ": "VALUE",
    "Nạp thêm {next_count} mục": "Load {next_count} more items",
    "Còn {remaining} mục": "{remaining} items remaining",
    "Nhấp đúp để nạp trang tiếp theo": "Double-click to load the next page",
    "Các mục còn lại không bị loại khỏi dữ liệu": "The remaining items are still included in the data",
    "Kéo thả tệp hoặc thư mục vào đây": "Drop files or folders here",
    "Có thể chọn nhiều tệp cùng lúc": "You can select multiple files at once",
    "＋  Thêm tệp": "＋  Add files",
    "＋  Thêm thư mục": "＋  Add folder",
    "Chuyển ảnh": "Image conversion",
    "Nén ZIP": "Create ZIP",
    "Giải nén": "Extract",
    "So sánh": "Compare",
    "Tệp đã chọn": "Selected files",
    "0 tệp  ·  0 B": "0 files  ·  0 B",
    "Xóa mục chọn": "Remove selected",
    "Xóa tất cả": "Clear all",
    "Danh sách đang trống": "The list is empty",
    "TÊN TỆP": "FILE NAME",
    "DUNG LƯỢNG": "SIZE",
    "Mức nén": "Compression",
    "Mỗi tệp ZIP sẽ được giải nén vào một thư mục riêng": "Each ZIP file will be extracted into a separate folder",
    "Định dạng": "Format",
    "Chất lượng": "Quality",
    "Tạo tệp ZIP  →": "Create ZIP  →",
    "Đang chuẩn bị…": "Preparing…",
    "Hủy tác vụ": "Cancel task",
    "Tùy chọn…": "Preferences…",
    "Lịch sử tác vụ…": "Task history…",
    "Mở thư mục cấu hình": "Open configuration folder",
    "Mở thư mục nhật ký": "Open log folder",
    "Thoát": "Quit",
    "Trợ giúp": "Help",
    "Giới thiệu FileForge": "About FileForge",
    "Mở FileForge": "Open FileForge",
    "Lịch sử tác vụ": "Task history",
    "Thoát FileForge": "Quit FileForge",
    "Dữ liệu văn bản": "Text data",
    "Không thể mở thư mục cấu hình": "Could not open the configuration folder",
    "<p>Công cụ desktop hỗ trợ xử lý tệp, dữ liệu văn bản và mã hóa.</p>": "<p>A desktop toolkit for file processing, text data, and encryption.</p>",
    "<p>File được xử lý trực tiếp trên máy tính của bạn.</p>": "<p>Files are processed locally on your computer.</p>",
    "FileForge vẫn đang chạy trong khay hệ thống.": "FileForge is still running in the system tray.",
    "Tác vụ đang chạy": "Task in progress",
    "Hãy chờ tác vụ hiện tại hoàn tất trước khi thoát FileForge.": "Wait for the current task to finish before quitting FileForge.",
    "Văn bản": "Text",
    "Cấu trúc": "Structure",
    "Chức năng": "Operation",
    "Tên lớp": "Class name",
    "Thực hiện  →": "Run  →",
    "ĐẦU VÀO": "INPUT",
    "Dán JSON hoặc XML vào đây…\n\nVí dụ JSON:\n{\n  \"name\": \"FileForge\",\n  \"active\": true\n}": "Paste JSON or XML here…\n\nJSON example:\n{\n  \"name\": \"FileForge\",\n  \"active\": true\n}",
    "KẾT QUẢ": "OUTPUT",
    "Kết quả sẽ hiển thị ở đây…": "The result will appear here…",
    "Sẵn sàng": "Ready",
    "Tìm trong kết quả…": "Find in results…",
    "Tìm kết quả trước": "Find previous",
    "Tìm kết quả tiếp theo": "Find next",
    "Thu gọn HTML": "Collapse HTML",
    "Mở rộng HTML": "Expand HTML",
    "Copy đầu vào": "Copy input",
    "Copy kết quả": "Copy result",
    "Nội dung đã thay đổi · hãy thực hiện lại để xem cấu trúc": "Content changed · run the operation again to refresh the structure",
    "Chưa có dữ liệu": "No data",
    "Dán JSON hoặc XML vào ô đầu vào trước.": "Paste JSON or XML into the input first.",
    "Đang xử lý trong luồng nền…": "Processing in the background…",
    "Không thể xử lý · kiểm tra dữ liệu đầu vào": "Could not process · check the input",
    "Không thể xử lý dữ liệu đầu vào": "Could not process the input data",
    "Xử lý dữ liệu thất bại": "Data processing failed",
    "Kiểm tra cú pháp JSON/XML/HTML": "Check the JSON/XML/HTML syntax",
    "Dữ liệu chưa hợp lệ": "Invalid data",
    "Không thể xử lý nội dung. Kiểm tra cú pháp JSON/XML/HTML rồi thử lại.\n\n": "Could not process the content. Check the JSON/XML/HTML syntax and try again.\n\n",
    "Wrap: Tắt": "Wrap: Off",
    "Wrap: Bật": "Wrap: On",
    "Xếp dọc": "Stack vertically",
    "Xếp ngang": "Arrange horizontally",
    "Đã sao chép nội dung đầu vào": "Input copied",
    "Đã xóa nội dung": "Content cleared",
    "Đã đưa hai khung về tỷ lệ 50/50": "Restored the two panes to a 50/50 split",
    "Đã thu gọn các thẻ HTML": "Collapsed HTML elements",
    "Đã mở rộng tất cả thẻ HTML": "Expanded all HTML elements",
    "Đã sao chép kết quả": "Result copied",
    "0 ký tự": "0 characters",
    "Dán JSON": "Paste JSON",
    "Mở tệp .json…": "Open .json file…",
    "Chọn dán JSON hoặc nạp nội dung từ tệp JSON trên máy": "Paste JSON or load it from a local JSON file",
    "Dán HTTP request đã copy từ DevTools hoặc tài liệu. FileForge sẽ tách METHOD, URL và HEADERS thành lệnh cURL.": "Paste an HTTP request copied from DevTools or documentation. FileForge will convert the METHOD, URL, and HEADERS into a cURL command.",
    "HTTP REQUEST  ·  METHOD / URL / HEADERS": "HTTP REQUEST  ·  METHOD / URL / HEADERS",
    "Dán request từ DevTools…\n\n": "Paste a request from DevTools…\n\n",
    "REQUEST BODY / PAYLOAD  ·  TÙY CHỌN": "REQUEST BODY / PAYLOAD  ·  OPTIONAL",
    "Dán JSON / protobuf / form body ở đây. Nội dung được giữ nguyên và đưa vào --data-raw…": "Paste a JSON, protobuf, or form body here. The content is preserved and passed to --data-raw…",
    "Lệnh cURL sẽ xuất hiện ở đây…": "The cURL command will appear here…",
    "Chuyển thành cURL  →": "Convert to cURL  →",
    "Copy cURL": "Copy cURL",
    "Xóa": "Clear",
    "Đã xóa": "Cleared",
    "Không thể phân tích request": "Could not parse the request",
    "Request chưa hợp lệ": "Invalid request",
    " · có body": " · with body",
    "Đã sao chép lệnh cURL": "cURL command copied",
    "Mã hóa và giải mã URL theo UTF-8 · xử lý hoàn toàn trên thiết bị": "Encode and decode URLs using UTF-8 · processed entirely on this device",
    "Nhập URL hoặc chuỗi cần chuyển đổi…": "Enter a URL or string to convert…",
    "Encode  →": "Encode  →",
    "←  Decode": "←  Decode",
    "⇄ Đổi bên": "⇄ Swap sides",
    "Đã encode URL": "URL encoded",
    "Đã decode URL": "URL decoded",
    "Chọn riêng giao diện Encode hoặc Decode · xử lý hoàn toàn offline": "Separate Encode and Decode workspaces · processed entirely offline",
    "Chỉ dùng khi bấm Tạo key. Key nhập tay được xác định kích thước từ số byte thực tế.": "Used only when generating a key. The size of a manually entered key is determined by its actual byte length.",
    "UTF-8 được dùng trực tiếp làm byte của key, không phải mật khẩu qua KDF. Key sau khi giải mã định dạng phải dài 16, 24 hoặc 32 byte. Key sinh dạng UTF-8 dễ đọc có entropy thấp hơn HEX/Base-64; nên chọn HEX/Base-64 để có key ngẫu nhiên đủ entropy.": "UTF-8 is used directly as key bytes, not as a password processed by a KDF. A decoded key must be 16, 24, or 32 bytes long. Readable UTF-8-generated keys have lower entropy than HEX/Base-64; use HEX/Base-64 for sufficiently random keys.",
    "IV/nonce UTF-8 được dùng trực tiếp làm byte. IV sinh dạng UTF-8 dễ đọc có entropy thấp hơn HEX/Base-64; nên chọn HEX/Base-64 để có IV ngẫu nhiên đủ entropy.": "UTF-8 IVs/nonces are used directly as bytes. Readable UTF-8-generated IVs have lower entropy than HEX/Base-64; use HEX/Base-64 for sufficiently random IVs.",
    "Key size (tạo key)": "Key size (generated key)",
    "Key theo định dạng đã chọn…": "Key in the selected format…",
    "Hiện": "Show",
    "Tạo key": "Generate key",
    "Tự sinh khi Encode; lưu lại để Decode": "Generated automatically on Encode; save it for Decode",
    "Tạo IV": "Generate IV",
    "Nhập plaintext cần mã hóa…": "Enter plaintext to encrypt…",
    "Ciphertext sẽ xuất hiện ở đây…": "Ciphertext will appear here…",
    "Dán ciphertext cần giải mã…": "Paste ciphertext to decrypt…",
    "Kết quả giải mã sẽ xuất hiện ở đây…": "The decrypted result will appear here…",
    "GCM có xác thực và nên được ưu tiên; GCM/CTR chỉ dùng NoPadding. Không tái sử dụng nonce/IV với cùng key trong GCM hoặc CTR. GCM xuất ciphertext kèm tag xác thực 16 byte ở cuối. CBC/ECB hỗ trợ NoPadding hoặc PKCS5Padding (PKCS7 cho block AES); CBC/CTR/ECB không tự xác thực ciphertext. ECB không phù hợp cho dữ liệu nhạy cảm. Key UTF-8 là byte trực tiếp, không qua KDF.": "GCM provides authentication and is recommended; GCM/CTR support NoPadding only. Never reuse a nonce/IV with the same key in GCM or CTR. GCM appends a 16-byte authentication tag to the ciphertext. CBC/ECB support NoPadding or PKCS5Padding (PKCS7 for AES blocks); CBC/CTR/ECB do not authenticate ciphertext. ECB is unsuitable for sensitive data. UTF-8 keys are used directly as bytes, without a KDF.",
    "Encrypt  →": "Encrypt  →",
    "←  Decrypt": "←  Decrypt",
    "Đã tạo key UTF-8 tiện nhập; entropy thấp hơn HEX/Base-64. Nên dùng HEX/Base-64 cho key ngẫu nhiên.": "Generated a readable UTF-8 key; entropy is lower than HEX/Base-64. Use HEX/Base-64 for a random key.",
    "Đã tạo key ngẫu nhiên bằng CSPRNG": "Random key generated using a CSPRNG",
    "ECB không sử dụng IV": "ECB does not use an IV",
    "Đã tạo IV UTF-8 tiện nhập; entropy thấp hơn HEX/Base-64. Nên dùng HEX/Base-64 cho IV ngẫu nhiên.": "Generated a readable UTF-8 IV; entropy is lower than HEX/Base-64. Use HEX/Base-64 for a random IV.",
    "Đã tạo IV/nonce ngẫu nhiên bằng CSPRNG": "Random IV/nonce generated using a CSPRNG",
    "GCM khuyến nghị IV 12 byte": "GCM recommends a 12-byte IV",
    "IV/counter 16 byte": "16-byte IV/counter",
    "Vui lòng nhập hoặc tạo AES key.": "Please enter or generate an AES key.",
    "Encode thành công · lưu lại key và IV/nonce để Decode": "Encoding succeeded · save the key and IV/nonce for decoding",
    "Decode thành công": "Decoding succeeded",
    "Đã sao chép": "Copied",
    "So sánh văn bản và JSON cục bộ — dữ liệu không rời khỏi máy": "Compare text and JSON locally — your data never leaves this device",
    "Độ chi tiết": "Granularity",
    "Theo dòng": "By line",
    "Theo từ": "By word",
    "Theo ký tự": "By character",
    "Bỏ qua hoa/thường": "Ignore case",
    "Bỏ qua khoảng trắng": "Ignore whitespace",
    "Bỏ qua dòng trống": "Ignore blank lines",
    "BẢN GỐC": "ORIGINAL",
    "Dán văn bản phiên bản ban đầu…": "Paste the original text…",
    "BẢN MỚI": "UPDATED",
    "Dán văn bản phiên bản đã chỉnh sửa…": "Paste the modified text…",
    "KẾT QUẢ SO SÁNH": "COMPARISON RESULT",
    "Nhập hai bản văn bản rồi chọn So sánh": "Enter both text versions and select Compare",
    "Các phần đã xóa sẽ được đánh dấu ở đây": "Removed content will be highlighted here",
    "Các phần được thêm sẽ được đánh dấu ở đây": "Added content will be highlighted here",
    "So sánh mảng": "Array comparison",
    "Theo vị trí": "By index",
    "Bỏ qua thứ tự": "Ignore order",
    "Theo vị trí: phần tử [0] so với [0]. Bỏ qua thứ tự: xem mảng như tập hợp có giữ số lần lặp.": "By index: compare element [0] with [0]. Ignore order: compare arrays as multisets, preserving duplicate counts.",
    "So sánh JSON": "Compare JSON",
    "Ví dụ": "Example",
    "JSON GỐC (A)": "ORIGINAL JSON (A)",
    "Dán JSON ban đầu vào đây…": "Paste the original JSON here…",
    "JSON MỚI (B)": "UPDATED JSON (B)",
    "Dán JSON đã thay đổi vào đây…": "Paste the updated JSON here…",
    "KHÁC BIỆT THEO CẤU TRÚC": "STRUCTURAL DIFFERENCES",
    "Object key được so sánh không phụ thuộc thứ tự": "Object keys are compared regardless of order",
    "Tất cả": "All",
    "Được thêm": "Added",
    "Đã sửa": "Modified",
    "LOẠI": "TYPE",
    "ĐƯỜNG DẪN": "PATH",
    "GIÁ TRỊ GỐC": "OLD VALUE",
    "GIÁ TRỊ MỚI": "NEW VALUE",
    "Copy báo cáo": "Copy report",
    "Chọn tệp JSON": "Select JSON file",
    "JSON (*.json);;Tất cả tệp (*)": "JSON (*.json);;All files (*)",
    "Không thể mở JSON": "Could not open JSON",
    "Hãy nhập nội dung ở cả hai bên": "Enter content on both sides",
    "Không thể so sánh": "Could not compare",
    "Thêm {result['added']} · Xóa {result['removed']} · Sửa {result['changed']}": "Added {result['added']} · Removed {result['removed']} · Modified {result['changed']}",
    "Hãy nhập JSON ở cả hai bên": "Enter JSON on both sides",
    "JSON không hợp lệ": "Invalid JSON",
    "Kiểm tra JSON đầu vào": "Check the input JSON",
    "THÊM": "ADDED",
    "XÓA": "REMOVED",
    "SỬA": "MODIFIED",
    "Hai tài liệu giống nhau": "The documents are identical",
    "So sánh hoàn tất": "Comparison complete",
    "Đã sao chép báo cáo": "Report copied",
    "Thêm nhiều tệp để gom vào một tệp ZIP": "Add files to bundle them into a ZIP archive",
    "Thêm tệp để bắt đầu nén": "Add files to start archiving",
    "＋  Chọn ZIP": "＋  Select ZIP files",
    "Kéo thả tệp ZIP vào đây": "Drop ZIP files here",
    "Có thể giải nén nhiều tệp ZIP cùng lúc": "You can extract multiple ZIP files at once",
    "Giải nén ZIP  →": "Extract ZIP  →",
    "Chọn một hoặc nhiều tệp ZIP": "Select one or more ZIP files",
    "＋  Chọn ảnh": "＋  Select images",
    "Kéo thả ảnh vào đây": "Drop images here",
    "Hỗ trợ PNG, JPG, WEBP, BMP và TIFF": "Supports PNG, JPG, WEBP, BMP, and TIFF",
    "Chuyển đổi ảnh  →": "Convert images  →",
    "Chọn ảnh cần chuyển đổi": "Select images to convert",
    "Chọn tệp ZIP": "Select ZIP files",
    "Chọn ảnh": "Select images",
    "Tất cả tệp (*)": "All files (*)",
    "Chọn tệp": "Select files",
    "Chọn thư mục": "Select folder",
    "Đang yêu cầu hủy an toàn…": "Requesting safe cancellation…",
    "Đã hủy tác vụ · giữ lại {count} kết quả đã hoàn tất": "Task cancelled · kept {count} completed result(s)",
    "Đã hủy · giữ lại {count} kết quả đã hoàn tất": "Cancelled · kept {count} completed result(s)",
    "Đã giữ lại {count} kết quả hoàn tất": "Kept {count} completed result(s)",
    "Đã hủy tác vụ · phần kết quả đang xử lý đã được dọn": "Task cancelled · temporary output from the active item was cleaned up",
    "Đã hủy theo yêu cầu người dùng": "Cancelled at the user's request",
    "FileForge đã dọn phần kết quả tạm": "FileForge cleaned up the temporary output",
    "Đã hủy tác vụ": "Task cancelled",
    "Chưa có tệp": "No files selected",
    "Hãy thêm tệp trước khi tiếp tục.": "Add files before continuing.",
    "Lưu tệp ZIP": "Save ZIP file",
    "Chọn nơi giải nén": "Choose extraction folder",
    "Chọn thư mục lưu ảnh": "Choose image output folder",
    "Nén ZIP": "Create ZIP",
    "Giải nén ZIP": "Extract ZIP",
    "Chuyển ảnh sang {output_format}": "Convert images to {output_format}",
    "Đang nén": "Creating ZIP",
    "Đang giải nén": "Extracting",
    "Đang chuyển đổi": "Converting",
    "Mở thư mục": "Open folder",
    "Đóng": "Close",
    "Đã tạo tệp ZIP": "ZIP file created",
    "Hoàn tất": "Completed",
    "Tệp ZIP đã được tạo thành công.": "The ZIP file was created successfully.",
    "Đã hoàn tất giải nén": "Extraction completed",
    "Hoàn tất giải nén": "Extraction complete",
    "Đã giải nén thành công {output_count} tệp ZIP.": "Successfully extracted {output_count} ZIP file(s).",
    "Đã hoàn tất chuyển đổi": "Conversion completed",
    "Hoàn tất chuyển đổi": "Conversion complete",
    "Đã chuyển đổi thành công {output_count} ảnh.": "Successfully converted {output_count} image(s).",
    "Hoàn tất {output_count} mục": "Completed {output_count} item(s)",
    "Tác vụ thất bại": "Task failed",
    "Không có tệp được xử lý": "No files processed",
    "Không có tệp nào được xử lý thành công. Xem lịch sử tác vụ để biết chi tiết.": "No files were processed successfully. See task history for details.",
    "Chi tiết lỗi": "Error details",
    "Tác vụ không thành công": "Task failed",
    "Có lỗi xảy ra": "An error occurred",
    "Không thể hoàn thành tác vụ.\n\n{message}": "The task could not be completed.\n\n{message}",
    "Đang khởi động…": "Starting…",
    "Đang dựng giao diện…": "Building the interface…",
    "Không thể khởi động FileForge": "Could not start FileForge",
    "Gần xong…": "Almost done…",
    "Ngôn ngữ": "Language",
    "Thay đổi ngôn ngữ có hiệu lực ngay lập tức và được lưu cho lần mở tiếp theo.": "Language changes take effect immediately and are saved for the next launch.",
    "Ngôn ngữ đã được cập nhật.": "The language has been updated.",
    "Chọn ngôn ngữ giao diện.": "Choose the interface language.",
    "Phiên bản": "Version",
    "Thời gian": "Time",
    "Tác vụ": "Task",
    "Trạng thái": "Status",
    "Số mục": "Items",
    "Thời lượng": "Duration",
    "Kết quả": "Result",
    "Lịch sử tác vụ – FileForge": "Task History – FileForge",
    "Tìm theo tác vụ, tên tệp hoặc trạng thái…": "Search by task, file name, or status…",
    "Mở thư mục kết quả": "Open output folder",
    "Chi tiết": "Details",
    "Xóa lịch sử": "Clear history",
    "Thành công": "Success",
    "Một phần": "Partial",
    "Thất bại": "Failed",
    "Đã hủy": "Cancelled",
    "Thành công": "Success",
    "Xóa toàn bộ lịch sử tác vụ trên máy này? Thao tác này không xóa các tệp kết quả.": "Clear all task history on this computer? This will not delete output files.",
    "Giấy phép": "License",
    "Giới thiệu": "About",
    "Tùy chọn FileForge": "FileForge Preferences",
    "Thiết lập cách FileForge ghi nhớ phiên làm việc và thư mục.": "Choose what FileForge remembers between sessions.",
    "Khôi phục kích thước cửa sổ và công cụ đã mở lần trước": "Restore the previous window size and selected tool",
    "Ghi nhớ thư mục gần nhất khi mở và lưu tệp": "Remember the last folder used to open and save files",
    "Ghi nhớ tùy chọn xử lý gần nhất (mức nén, định dạng và chất lượng ảnh)": "Remember the last processing options (compression, format, and image quality)",
    "Thu nhỏ FileForge xuống khay hệ thống khi nhấn nút đóng": "Minimize FileForge to the system tray when the close button is pressed",
    "Khay hệ thống hiện không khả dụng trên môi trường này.": "The system tray is not available in this environment.",
    "Hiển thị thông báo khi tác vụ hoàn tất trong lúc ứng dụng đang ẩn": "Show notifications when tasks finish while the app is hidden",
    "Thư mục đầu ra ưu tiên": "Preferred output folder",
    "Thư mục này được dùng làm vị trí gợi ý khi lưu ZIP hoặc giải nén/chuyển ảnh. Để trống để dùng thư mục gần nhất hoặc thư mục cá nhân.": "This folder is suggested when saving ZIP files or extracting/converting images. Leave it empty to use the last folder or your home folder.",
    "Mặc định: thư mục gần nhất": "Default: last used folder",
    "Duyệt…": "Browse…",
    "Chọn thư mục đầu ra ưu tiên": "Choose preferred output folder",
    "Thư mục không hợp lệ": "Invalid folder",
    "Thư mục đầu ra đã chọn không tồn tại hoặc không thể truy cập.": "The selected output folder does not exist or cannot be accessed.",
    "Chọn thư mục đầu ra": "Choose output folder",
    "Lưu": "Save",
    "Hủy": "Cancel",
    "Đảo chiều chuyển đổi và đưa kết quả hiện tại về ô đầu vào": "Reverse the conversion direction and move the current result to the input",
    "Đã xóa nội dung": "Content cleared",
    "Đã đưa hai khung về tỷ lệ 50/50": "Restored the two panes to a 50/50 split",
    "Đã nạp {filename}": "Loaded {filename}",
    "Chọn tệp": "Select files",
    "KÉT QUẢ": "RESULT",
    "Tổng số": "Total",
    "Giới thiệu": "About",
}

_REVERSE = {english: source for source, english in ENGLISH.items()}


def set_language(language: str) -> None:
    """Set the active UI language; unsupported values fall back to Vietnamese."""
    global _current_language
    _current_language = language if language in SUPPORTED_LANGUAGES else "vi"


def get_language() -> str:
    return _current_language


def translate_text(value: Any) -> Any:
    """Translate a UI string while leaving arbitrary non-string values untouched."""
    if not isinstance(value, str) or _current_language == "vi":
        if isinstance(value, str) and _current_language == "vi":
            return _REVERSE.get(value, value)
        return value
    translated = ENGLISH.get(value)
    if translated is not None:
        return translated
    return _translate_dynamic(value)


def _translate_dynamic(value: str) -> str:
    """Translate common status and task labels that contain runtime values."""
    if _current_language == "vi":
        reversed_patterns = (
            (r"^Added (\d+) · Removed (\d+) · Modified (\d+)$", r"Thêm \1 · Xóa \2 · Sửa \3"),
            (r"^(\d+) differences  ·  \+(\d+) added  ·  −(\d+) removed  ·  ~(\d+) modified$", r"\1 khác biệt  ·  +\2 thêm  ·  −\3 xóa  ·  ~\4 sửa"),
            (r"^(\d[\d,]*) files  ·  (.+)$", r"\1 tệp  ·  \2"),
            (r"^([\d,]+) characters$", r"\1 ký tự"),
            (r"^Completed · ([\d,]+) input characters$", r"Hoàn tất · \1 ký tự đầu vào"),
            (r"^([\d,]+) input characters → ([\d,]+) output characters$", r"\1 ký tự đầu vào → \2 ký tự đầu ra"),
            (r"^([\d,]+) → ([\d,]+) characters$", r"\1 → \2 ký tự"),
            (r"^Created (.+)$", r"Đã tạo \1"),
            (r"^Loaded (.+)$", r"Đã nạp \1"),
            (r"^Creating ZIP: (.+)$", r"Đang nén: \1"),
            (r"^Extracting: (.+)$", r"Đang giải nén: \1"),
            (r"^Converting: (.+)$", r"Đang chuyển đổi: \1"),
            (r"^Error: (.+)$", r"Lỗi: \1"),
            (r"^Could not encode: (.+)$", r"Không thể encode: \1"),
            (r"^Could not decode: (.+)$", r"Không thể decode: \1"),
            (r"^Recognized (.+)$", r"Đã nhận diện \1"),
            (r"^Process data: (.+)$", r"Xử lý dữ liệu: \1"),
            (r"^Completed (\d+) item\(s\)$", r"Hoàn tất \1 mục"),
            (r"^Successfully extracted (\d+) ZIP file\(s\)\.$", r"Đã giải nén thành công \1 tệp ZIP."),
            (r"^Successfully converted (\d+) image\(s\)\.$", r"Đã chuyển đổi thành công \1 ảnh."),
            (r"^([\d,.]+) seconds$", r"\1 giây"),
            (r"^(\d+) recent task\(s\)$", r"\1 tác vụ gần đây"),
            (r"^(\d+)/(\d+) task\(s\)$", r"\1/\2 tác vụ"),
            (r"^Task cancelled · kept (\d+) completed result\(s\)$", r"Đã hủy tác vụ · giữ lại \1 kết quả đã hoàn tất"),
        )
        for pattern, replacement in reversed_patterns:
            if re.match(pattern, value):
                return re.sub(pattern, replacement, value)
        return _REVERSE.get(value, value)

    patterns = (
        (r"^(\d[\d,]*) tệp  ·  (.+)$", r"\1 files  ·  \2"),
        (r"^([\d,]+) ký tự$", r"\1 characters"),
        (r"^Hoàn tất · ([\d,]+) ký tự đầu vào$", r"Completed · \1 input characters"),
        (r"^([\d,]+) ký tự đầu vào → ([\d,]+) ký tự đầu ra$", r"\1 input characters → \2 output characters"),
        (r"^([\d,]+) → ([\d,]+) ký tự$", r"\1 → \2 characters"),
        (r"^Thêm (\d+) · Xóa (\d+) · Sửa (\d+)$", r"Added \1 · Removed \2 · Modified \3"),
        (r"^(\d+) khác biệt  ·  \+(\d+) thêm  ·  −(\d+) xóa  ·  ~(\d+) sửa$", r"\1 differences  ·  +\2 added  ·  −\3 removed  ·  ~\4 modified"),

        (r"^(\d[\d,]*) tệp  ·  (.+)$", r"\1 files  ·  \2"),
        (r"^([\d,]+) ký tự$", r"\1 characters"),
        (r"^Hoàn tất · ([\d,]+) ký tự đầu vào$", r"Completed · \1 input characters"),
        (r"^([\d,]+) ký tự đầu vào → ([\d,]+) ký tự đầu ra$", r"\1 input characters → \2 output characters"),
        (r"^([\d,]+) → ([\d,]+) ký tự$", r"\1 → \2 characters"),
        (r"^Đã tạo (.+)$", r"Created \1"),
        (r"^Đã nạp (.+)$", r"Loaded \1"),
        (r"^Đang nén: (.+)$", r"Creating ZIP: \1"),
        (r"^Đang giải nén: (.+)$", r"Extracting: \1"),
        (r"^Đang chuyển đổi: (.+)$", r"Converting: \1"),
        (r"^Lỗi: (.+)$", r"Error: \1"),
        (r"^Không thể encode: (.+)$", r"Could not encode: \1"),
        (r"^Không thể decode: (.+)$", r"Could not decode: \1"),
        (r"^Đã nhận diện (.+)$", r"Recognized \1"),
        (r"^Xử lý dữ liệu: (.+)$", r"Process data: \1"),
        (r"^Hoàn tất (\d+) mục$", r"Completed \1 item(s)"),
        (r"^Đã giải nén thành công (\d+) tệp ZIP\.$", r"Successfully extracted \1 ZIP file(s)."),
        (r"^Đã chuyển đổi thành công (\d+) ảnh\.$", r"Successfully converted \1 image(s)."),
        (r"^([\d,.]+) giây$", r"\1 seconds"),
        (r"^(\d+) tác vụ gần đây$", r"\1 recent task(s)"),
        (r"^(\d+)/(\d+) tác vụ$", r"\1/\2 task(s)"),
        (r"^Đã hủy tác vụ · giữ lại (\d+) kết quả đã hoàn tất$", r"Task cancelled · kept \1 completed result(s)"),
    )
    for pattern, replacement in patterns:
        if re.match(pattern, value):
            return re.sub(pattern, replacement, value)
    return value

def translate_object_tree(root: QWidget) -> None:
    """Translate visible widget text, placeholders, menus, tabs, and table headers."""
    objects = [root, *root.findChildren(QWidget), *root.findChildren(QAction), *root.findChildren(QMenu)]
    seen: set[int] = set()
    for obj in objects:
        marker = id(obj)
        if marker in seen:
            continue
        seen.add(marker)

        if isinstance(obj, (QMainWindow, QDialog, QWidget)):
            title = obj.windowTitle()
            if title:
                obj.setWindowTitle(translate_text(title))
            tooltip = obj.toolTip()
            if tooltip:
                obj.setToolTip(translate_text(tooltip))

        if isinstance(obj, QLabel):
            obj.setText(translate_text(obj.text()))
        elif isinstance(obj, QAbstractButton):
            obj.setText(translate_text(obj.text()))

        if isinstance(obj, QLineEdit):
            obj.setPlaceholderText(translate_text(obj.placeholderText()))
        elif isinstance(obj, (QPlainTextEdit, QTextEdit)):
            obj.setPlaceholderText(translate_text(obj.placeholderText()))

        if isinstance(obj, QComboBox):
            for index in range(obj.count()):
                obj.setItemText(index, translate_text(obj.itemText(index)))

        if isinstance(obj, QTabWidget):
            for index in range(obj.count()):
                obj.setTabText(index, translate_text(obj.tabText(index)))
        elif isinstance(obj, QTabBar):
            for index in range(obj.count()):
                obj.setTabText(index, translate_text(obj.tabText(index)))

        if isinstance(obj, QTableWidget):
            for column in range(obj.columnCount()):
                item = obj.horizontalHeaderItem(column)
                if item is not None:
                    item.setText(translate_text(item.text()))

        if isinstance(obj, QTreeWidget):
            header = obj.headerItem()
            if header is not None:
                for column in range(obj.columnCount()):
                    header.setText(column, translate_text(header.text(column)))

        if isinstance(obj, QAction):
            obj.setText(translate_text(obj.text()))
        elif isinstance(obj, QMenu):
            obj.setTitle(translate_text(obj.title()))
