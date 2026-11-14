# FileForge

Ứng dụng desktop gọn nhẹ để gom tệp, nén/giải nén ZIP và chuyển đổi ảnh. Xây dựng bằng Python và PySide6.

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
- Tự xử lý ảnh có kênh trong suốt khi xuất JPG bằng nền trắng.
- Giữ hướng ảnh theo EXIF và hồ sơ màu ICC khi có thể.
- Tự đổi tên khi tệp đầu ra đã tồn tại; bỏ qua ảnh lỗi và tiếp tục batch.

## Yêu cầu

- Python 3.10 trở lên (khuyến nghị Python 3.12).
- PySide6.
- Pillow.

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
- tests/ — kiểm thử tự động.

## Quyền riêng tư

FileForge xử lý tệp trực tiếp trên máy tính. Ứng dụng không tải tệp của bạn lên máy chủ.
