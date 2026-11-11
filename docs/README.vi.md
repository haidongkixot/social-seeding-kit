# Social Seeding Kit

Plugin của Claude Code giúp một người seeding thương hiệu trong các nhóm và fanpage Facebook mà không vi phạm quy tắc của nhóm lẫn của Facebook. Claude tìm các bài phù hợp, soạn câu trả lời hợp với từng cuộc trò chuyện, đối chiếu với thông tin bạn đã duyệt, rồi đưa cho bạn một danh sách đánh số. **Bạn duyệt từng mục. Claude không tự đăng gì.**

Một trang web (trung tâm điều khiển) là nơi bạn thiết lập hệ thống, đánh dấu duyệt, tạm dừng và theo dõi kết quả.

Ngôn ngữ của trang và tài liệu: English ([README.en.md](README.en.md)), Tiếng Việt, Español ([README.es.md](README.es.md)).

## Bạn có gì
- **Scout**: đọc các bài mới nhất của các nhóm đang hoạt động (chỉ đọc) và chấm điểm mức phù hợp.
- **Conversation manager**: theo dõi mỗi cuộc trò chuyện từ phản hồi đầu tiên đến lời mời (Gieo mầm, Có tương tác, Đủ điều kiện, Đã mời, Đã tham gia).
- **Người viết, người kiểm duyệt, quản lý rủi ro**: soạn nháp, kiểm tra thông tin và giọng văn, giữ hàng đợi trong giới hạn mỗi ngày, nhịp đăng và thời gian làm quen. Kiểm tra sức khỏe xếp tài khoản XANH, VÀNG hoặc ĐỎ.
- **Trung tâm điều khiển** (trang do Claude xuất bản): Thiết lập, Kênh, Duyệt bài, Bảng theo dõi, Điều khiển.
- **Báo cáo** hai tuần một lần, kèm đề xuất dựa trên số liệu.

## Cài đặt
Xem [INSTALL.md](INSTALL.md). Tóm tắt:
```
/plugin marketplace add <đường-dẫn-hoặc-repo-github>
/plugin install social-seeding@social-seeding-kit
```
Sau đó, trong một thư mục trống, mở Claude Code và chạy `/social-seeding:seeding-setup`.

## Thiết lập (một lần cho mỗi thương hiệu)
1. `/seeding-setup` kiểm tra công cụ, hỏi vài câu và tạo thư mục **workspace** (cấu hình, thông tin, playbook, lượt chạy, cuộc trò chuyện). Dữ liệu của bạn nằm ở đó; cập nhật plugin không bao giờ đụng tới.
2. Nó xuất bản **trung tâm điều khiển**. Mở tab **Thiết lập**: thương hiệu và người đại diện, nhóm hàng, đích của phễu (mỗi nhóm hàng một nhóm WhatsApp, Telegram, Zalo, Messenger hoặc website), ngôn ngữ, thông tin, kênh, giới hạn và lịch chạy.
3. Chạy `/sync-control`. Các chỉnh sửa của bạn được ghi vào workspace và kiểm tra hợp lệ.
4. Ngày đầu chỉ **soạn nháp**: bạn xem bản nháp, chưa thể đăng gì.

## Nhịp làm việc hằng ngày
| Khi nào | Lệnh | Việc xảy ra |
|---|---|---|
| Buổi sáng | `/daily-run` | Kiểm tra sức khỏe, quét, soạn nháp, kiểm duyệt và rà rủi ro. Hàng đợi hiện ở tab Duyệt bài. |
| Sau khi xem | đánh dấu trên trang rồi nhắn Claude "đã duyệt như đã đánh dấu", hoặc trả lời "duyệt 1-5; sửa 3: ...; bỏ 6" | Claude hiện lại những gì bạn đã duyệt và `/post-approved` chỉ đăng đúng những mục đó, giãn cách, đúng danh tính. |
| Buổi chiều | `/hot-replies` | Rà lại lần nữa để tìm bài mua mới. |
| Mỗi giờ | `/check-replies` | Bình luận và tin nhắn mới, lấy từ email thông báo Facebook khi đã nối Gmail. Soạn trả lời và báo cho bạn. |
| Bất cứ lúc nào | `/health-check`, `/sync-control`, `/publish-status` | Sức khỏe tài khoản, áp dụng chỉnh sửa từ trang, làm mới bảng theo dõi. |
| Thứ Sáu cách tuần | `/biweekly-report` | Báo cáo phễu, chất lượng, rủi ro và kênh. |

## Quy tắc an toàn (cố định)
Nằm trong `plugins/social-seeding/SAFETY.md` và không thể đổi bằng cấu hình, trang web hay chat.
1. Chỉ dùng danh tính thật, nêu rõ: trang cá nhân của bạn, kèm vai trò thương hiệu. Không dùng tài khoản giả.
2. Không đăng gì khi chưa có sự đồng ý của bạn trong chat. Dấu duyệt trên trang chỉ là đề xuất.
3. Claude không bao giờ đăng nhập, không xử lý 2FA hay CAPTCHA, và chỉ tham gia nhóm khi bạn yêu cầu.
4. Chỉ hành xử tuân thủ: giới hạn, nhịp đăng, độ liên quan, làm quen. Không né tránh phát hiện.
5. Thông tin chỉ lấy từ các tệp knowledge đã duyệt.
6. Không nhắn tin riêng cho người lạ.
7. Ở bảng rao vặt sỉ: chỉ trả lời bài mua, tối đa một bài chào hàng mỗi ngày, chỉ gắn liên kết sau thời gian làm quen.
8. Không thu thập dữ liệu cá nhân ngoài những người đã tương tác với bạn và thông tin liên hệ họ tự cung cấp.

## Việc bạn phải tự làm
- Đăng nhập Facebook trên trình duyệt mà Claude in Chrome sử dụng và giữ trạng thái đăng nhập.
- Tự tham gia các nhóm và fanpage, từng đợt một, rồi đặt từng kênh là Đang hoạt động kèm ngày tham gia.
- Duyệt từng ngôn ngữ trước khi dùng thật (người thành thạo, hoặc chính bạn).
- Duyệt thông tin: tích chọn trên trang.
- Mỗi tuần nhập số thành viên của từng đích phễu (số người tham gia được đo từ đó).
- Tùy chọn: nối Gmail và bật email thông báo của Facebook.

## Cấu trúc thư mục
```
plugins/social-seeding/   plugin: agent, skill, script, trang, mẫu, SAFETY.md
workspace/ (của bạn)      config/*.toml, knowledge/, playbooks/, runs/, conversations/, leads.csv, risk/, reports/
```
Các tệp cấu hình: `brand.toml`, `catalog.toml`, `funnel.toml`, `channels.toml`, `caps.toml` (có `[languages]`), `keywords.toml`. `python scripts/validate.py` kiểm tra tất cả.
