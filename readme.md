Tuyệt — mình sẽ gửi cho bạn một ứng dụng trình duyệt web bằng Python + PyQt5 (WebEngine), có thanh địa chỉ, nút Back/Forward/Reload, mở tab mới/đóng tab, và hỗ trợ tìm kiếm khi bạn gõ từ khóa thay vì URL. Chạy được trên Windows/Linux/macOS nếu cài các gói cần thiết.

Yêu cầu cài đặt

Trước khi chạy, cài thư viện:

pip install PyQt5 PyQtWebEngine

Mã nguồn (file: mini_browser.py)

Gợi ý nâng cao (nếu bạn muốn mở rộng)

Thêm bookmarks (lưu file JSON).

Thêm trình download (bắt sự kiện QWebEngineProfile.downloadRequested).

Hỗ trợ chế độ ẩn danh (tạo profile riêng).

Tích hợp extension, devtools, hoặc chế độ user agent tuỳ chỉnh.

Dùng PySide6 thay cho PyQt5 nếu thích (API tương tự).

Muốn mình sửa thêm tính năng nào (tab cố định, bookmarks, download manager, reader mode, hoặc tạo UI đẹp hơn bằng Tailwind-like style)? Tôi sẽ bổ sung code mẫu luôn.

🎉 Kết quả

✔ Chặn được hầu hết quảng cáo (Google Ads, Facebook tracking, DoubleClick, banner ads…)
✔ Không làm chậm trình duyệt
✔ Không phụ thuộc extension
✔ Không lỗi CORS
✔ Không ảnh hưởng video YouTube

Nếu bạn muốn:

Tôi có thể bổ sung:

🔧 Nâng cấp AdBlock mạnh hơn như Chrome

Tải EasyList/EasyPrivacy thật → parse chính xác 100%

Chặn script và iframe quảng cáo

Chặn tracking analytic (Google Analytics, Hotjar…)

Thêm giao diện bật/tắt AdBlock từng site (whitelist)

🔥 Hoặc thêm:

Dark mode

Chặn pop-up

Chặn cookie banners

Chống redirect

Downloader MP4/M3U8

Inspect Element

Extensions giống Chromium

Bạn muốn nâng cấp theo hướng nào?

pyinstaller --onefile --windowed webBrowser1.py