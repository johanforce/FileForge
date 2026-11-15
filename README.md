# FileForge

Ứng dụng desktop gọn nhẹ để gom tệp, nén/giải nén ZIP, chuyển đổi ảnh và xử lý JSON/XML. Xây dựng bằng Python và PySide6.

## Tính năng

### Nén ZIP
- Thêm nhiều tệp hoặc thêm toàn bộ tệp trong một thư mục.
- Kéo thả tệp và thư mục trực tiếp vào cửa sổ.
- Ba mức nén: nhanh nhất, cân bằng và nén tối đa.
- Giữ cấu trúc thư mục tương đối trong tệp ZIP.
- Hiển thị tiến trình nén; xử lý chạy nền để không khóa giao diện.

### Giải nén ZIP
- Giải nén một hoặc nhiều tệp ZIP trong một lần.
- Mỗi tệp ZIP được giải nén vào một thư mục riêng để tránh trùng tên.
- Kiểm tra đường dẫn và từ chối mục ZIP có đường dẫn vượt khỏi thư mục đích.
- Từ chối symbolic link và tiếp tục xử lý các tệp ZIP hợp lệ khác nếu một tệp bị lỗi.

### Chuyển đổi ảnh
- Đầu ra: JPG, PNG và WEBP.
- Đầu vào: PNG, JPG/JPEG, WEBP, BMP và TIFF.
- Chọn chất lượng JPG/WEBP từ 50% đến 100%.
- Xử lý ảnh trong suốt khi xuất JPG bằng nền trắng.
- Giữ hướng ảnh theo EXIF và hồ sơ màu ICC khi có thể.
- Tự đổi tên khi tệp đầu ra đã tồn tại; bỏ qua ảnh lỗi và tiếp tục batch.

### Công cụ JSON / XML / HTML
- JSON Format ⇄ Minify: định dạng dễ đọc hoặc loại bỏ khoảng trắng thừa.
- JSON ⇄ String: chuyển JSON thành chuỗi đã escape và giải mã ngược lại.
- JSON ⇄ XML: chuyển đổi hai chiều, hỗ trợ thuộc tính XML qua `@attributes`, nội dung hỗn hợp qua `#text` và các phần tử lặp thành mảng.
- XML Format ⇄ Minify: định dạng hoặc rút gọn XML.
- String ⇄ HTML: escape/unescape dấu gạch chéo ngược, dấu nháy kép, xuống dòng, carriage return và tab; HTML được định dạng theo cấu trúc thẻ.
- XML ⇄ String: kiểm tra XML và chuyển đổi giữa XML thô với nội dung chuỗi.
- JSON → Model: sinh Python dataclass, Pydantic v2 hoặc TypeScript interface.
- Các cặp chuyển đổi có tab riêng và nút đảo chiều; hỗ trợ Indent 2/4 spaces.
- HTML có tô màu cú pháp, tách dòng thuộc tính khi có nhiều thuộc tính, tìm kiếm, thu gọn/mở rộng, Copy và bật/tắt Wrap.
- Hỗ trợ object lồng nhau, mảng, trường có thể thiếu và giá trị null; JSON root dạng mảng/scalar được bọc trong `root`.

### Hiển thị cấu trúc và hiệu năng
- Hai vùng đầu vào/đầu ra, có thể chuyển giữa văn bản và cây JSON.
- Object và array có thể bung/thu theo từng cấp.
- Cây JSON nạp con theo yêu cầu, hiển thị 300 mục mỗi trang và có thể nạp tiếp; không bỏ mất field trong JSON lớn.
- Parse, format, chuyển đổi và sinh model chạy trong QThread; giao diện không phải chờ xử lý đồng bộ.
- Ô nhập không đặt giới hạn ký tự cố định; đã kiểm thử nhập và xử lý JSON có chuỗi 150.000 ký tự.
- Lỗi cú pháp JSON/XML được báo riêng, không làm ứng dụng thoát.

## Yêu cầu

- Python 3.10 trở lên (khuyến nghị Python 3.12).
- PySide6.
- Pillow.
- Pydantic v2 chỉ cần cài trong dự án đích nếu chọn xuất model Pydantic; FileForge không cần Pydantic để chạy.

## Cài đặt và chạy trên macOS

Cài Python 3.12 bằng Homebrew:

~~~bash
brew install python@3.12
~~~

Trong Terminal:

~~~bash
git clone https://github.com/johanforce/FileForge.git
cd FileForge

python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install --no-compile -r requirements.txt
python main.py
~~~

Tham số --no-compile giúp pip bỏ qua bước biên dịch các tệp template .tmpl.py đi kèm PySide6 trên một số môi trường macOS.

Nếu .venv cũ được tạo bằng Python 3.9, hãy xóa và tạo lại bằng Python 3.12:

~~~bash
deactivate 2>/dev/null || true
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --no-compile -r requirements.txt
~~~

## Cài đặt và chạy trên Windows

~~~powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
~~~

## Cài đặt và chạy trên Linux

~~~bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
~~~

## Chạy kiểm thử

~~~bash
python -m unittest discover -s tests -v
~~~

## Cấu trúc dự án

- main.py — giao diện desktop PySide6.
- fileforge/archive.py — bộ xử lý tạo tệp ZIP.
- fileforge/extraction.py — giải nén ZIP có kiểm tra đường dẫn.
- fileforge/images.py — chuyển đổi ảnh bằng Pillow.
- fileforge/text_utils.py — chuyển đổi/định dạng JSON và XML.
- fileforge/models.py — sinh model từ JSON.
- tests/ — kiểm thử tự động.

## Quyền riêng tư

FileForge xử lý tệp trực tiếp trên máy tính. Ứng dụng không tải tệp của bạn lên máy chủ.