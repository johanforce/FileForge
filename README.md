# FileForge

Ứng dụng desktop gọn nhẹ để gom tệp và tạo tệp ZIP, xây dựng bằng Python và PySide6.

## Tính năng hiện có

- Giao diện tiếng Việt, tối giản và tập trung vào thao tác.
- Thêm nhiều tệp hoặc thêm toàn bộ tệp trong một thư mục.
- Kéo thả tệp và thư mục trực tiếp vào cửa sổ.
- Xem danh sách tệp, biểu tượng và dung lượng.
- Xóa các mục đã chọn hoặc xóa toàn bộ danh sách.
- Tạo ZIP với ba mức nén: nhanh nhất, cân bằng và nén tối đa.
- Tiến trình nén chạy nền, không khóa giao diện.
- Giữ cấu trúc thư mục tương đối trong tệp ZIP.
- Kiểm tra tệp ZIP sau khi tạo trước khi lưu kết quả.

## Chưa triển khai

Chức năng chuyển đổi định dạng đang nằm trong kế hoạch, chưa có trong phiên bản này. Phiên bản hiện tại tập trung hoàn thiện thao tác gom tệp và nén ZIP.

## Yêu cầu

- Python 3.10 trở lên (khuyến nghị Python 3.12).
- PySide6.

## Cài đặt và chạy trên macOS

Cài Python 3.12 bằng Homebrew:

~~~bash
brew install python@3.12
~~~

Trong Terminal, tải dự án và tạo môi trường riêng:

~~~bash
git clone https://github.com/johanforce/FileForge.git
cd FileForge

python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install --no-compile -r requirements.txt
python main.py
~~~

Tham số --no-compile giúp pip bỏ qua bước biên dịch các tệp template .tmpl.py đi kèm PySide6.

Nếu đã có thư mục .venv được tạo bằng Python cũ, hãy xóa và tạo lại bằng Python 3.12:

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

Phần xử lý ZIP chỉ sử dụng thư viện chuẩn của Python, vì vậy không cần cài PySide6 để chạy kiểm thử:

~~~bash
python -m unittest discover -s tests -v
~~~

## Cấu trúc dự án

- main.py — giao diện desktop PySide6.
- fileforge/archive.py — bộ xử lý tạo tệp ZIP.
- tests/ — kiểm thử tự động.

## Quyền riêng tư

FileForge xử lý tệp trực tiếp trên máy tính. Ứng dụng không tải tệp của bạn lên máy chủ.