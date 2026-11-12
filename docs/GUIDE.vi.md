# Social Seeding Kit: hướng dẫn cài đặt và sử dụng

Hướng dẫn này đưa bạn từ một máy tính trống đến nhịp làm việc hằng ngày. Lần thiết lập đầu tiên mất khoảng một giờ. Bản tiếng Anh: [GUIDE.en.md](GUIDE.en.md).

**Quy tắc quan trọng nhất:** Claude soạn, bạn quyết. Không có bài nào được đăng, không tham gia nhóm nào, không nhắn tin cho ai nếu bạn chưa đồng ý trong khung chat Claude Code.

---

## Phần 1. Chuẩn bị

| Cần gì | Để làm gì | Cách kiểm tra |
|---|---|---|
| Claude Code (CLI hoặc ứng dụng desktop) | Chạy bộ kit | `claude --version` |
| Tiện ích Claude in Chrome, đã kết nối | Claude đọc Facebook trên trình duyệt của bạn | Claude Code liệt kê trình duyệt đã kết nối |
| Tài khoản Facebook đã đăng nhập và là thành viên các nhóm | Danh tính dùng để viết | Mở facebook.com trên trình duyệt đó |
| Python 3.11 trở lên | Các script của kit | `python --version` |
| `pip install openpyxl Pillow tzdata` | Bảng duyệt, hình ảnh, múi giờ | `python -c "import openpyxl, PIL, zoneinfo"` |
| git | Workspace là một thư mục git | `git --version` |
| Chrome hoặc Edge | Ảnh xem trước trong bảng duyệt | Thường đã có sẵn |
| Quyền truy cập repo riêng `haidongkixot/social-seeding-kit` | Để cài plugin | Nhờ chủ repo mời tài khoản GitHub của bạn |
| Tùy chọn: kết nối Gmail | Kiểm tra phản hồi mỗi giờ nhẹ hơn | Bật thêm email thông báo của Facebook |

---

## Cài nhanh (một lệnh)

```
git clone https://github.com/haidongkixot/social-seeding-kit.git
cd social-seeding-kit
setup.cmd            (Windows)
./setup.sh           (macOS / Linux)
```

Lệnh hỏi tên thương hiệu, rồi tự làm phần còn lại:
- cài các gói Python;
- tạo thư mục workspace `../<thương-hiệu>-seeding`;
- đăng ký plugin với Claude Code chỉ cho thư mục đó;
- mở Claude Code với `/social-seeding:seeding-setup`.

Claude xuất bản trung tâm điều khiển và đưa bạn đường dẫn: mở ra và điền tab **Thiết lập** (Phần 4). Chỉ cần cài sẵn Python 3.11+, git và Claude Code. Tùy chọn: `python bootstrap.py --help`.

Phần 2 bên dưới mô tả các bước tương tự nếu bạn muốn tự làm tay.

## Phần 2. Cài plugin

### 2.1 Tạo thư mục workspace
Mỗi thương hiệu một thư mục, ví dụ `D:\Seeding\acme`. Để trống.

### 2.2 Thêm marketplace và cài đặt
Mở terminal **trong thư mục đó** và chạy:

```
claude plugin marketplace add haidongkixot/social-seeding-kit
claude plugin install social-seeding@social-seeding-kit --scope local
```

(Nếu dùng bản sao trên máy: `claude plugin marketplace add "D:\duong-dan\social-seeding-kit"`.)

**Vì sao dùng `--scope local`:** plugin chỉ chạy trong thư mục này. Nếu cài cho cả tài khoản, nó có thể trùng tên với dự án khác có skill `daily-run` hoặc `scout` riêng.

Kiểm tra:
```
claude plugin details social-seeding@social-seeding-kit
```
Bạn sẽ thấy 9 skill và 6 agent.

### 2.3 Kiểm tra điều kiện
```
python "<thư mục plugin>\scripts\setup_workspace.py" prereqs
```
Mọi dòng phải là `"ok": true`. Sửa dòng nào chưa đạt (thường chỉ cần `pip install`). `/seeding-setup` cũng tự chạy bước này.

---

## Phần 3. Thiết lập lần đầu (mỗi thương hiệu một lần)

Mở Claude Code trong thư mục workspace và gõ:

```
/social-seeding:seeding-setup
```

Claude dẫn bạn qua 7 bước:

1. **Điều kiện.** Kiểm tra công cụ và hỏi bạn đã đăng nhập Facebook chưa.
2. **Workspace.** Hỏi trong một tin nhắn:
   - tên thương hiệu, tên người đại diện (người thật có trang cá nhân dùng để viết);
   - email chủ sở hữu;
   - ngôn ngữ giao diện: `en`, `vi` hoặc `es`;
   - múi giờ của bạn và của khán giả, ví dụ `Asia/Ho_Chi_Minh` và `Europe/Madrid`;
   - các ngôn ngữ dùng trong nhóm, ví dụ `en`, `vi`, `es-419`;
   - các nhóm hàng, ví dụ `home=Đồ gia dụng`.

   Sau đó Claude tạo thư mục, playbook, hướng dẫn văn phong và khởi tạo git.
3. **Trung tâm điều khiển.** Claude xuất bản trang điều khiển riêng của bạn và lưu đường dẫn vào `config/brand.toml`.
4. **Cấu hình.** Bạn điền tab Thiết lập trên trang (Phần 4), sau đó Claude chạy `/sync-control` để áp dụng.
5. **Tìm kênh** (tùy chọn). Claude tìm các nhóm công khai phù hợp; bạn chọn nhóm nào dùng.
6. **Lịch chạy** (tùy chọn). Claude đề xuất các lượt chạy định kỳ và chỉ tạo khi bạn đồng ý từng lượt.
7. **Ngày đầu chỉ soạn nháp.** Mọi thứ là bản nháp có đánh dấu cho đến khi thông tin và ngôn ngữ được duyệt.

---

## Phần 4. Trung tâm điều khiển

Mở đường dẫn Claude đưa, hoặc xem `control_center_url` trong `config/brand.toml`. Trang là riêng tư: chỉ bạn và các Editor bạn mời mới sửa được. Người được chia sẻ quyền xem chỉ đọc được.

### Tab Thiết lập (8 bước)
| Bước | Điền gì | Mẹo |
|---|---|---|
| Thương hiệu và người đại diện | Tên, email, câu giới thiệu vai trò, múi giờ | Câu giới thiệu, ví dụ "Mình là {rep}, bên {brand}.", mở đầu mọi tin nhắn đầu tiên |
| Nhóm hàng | Mỗi dòng sản phẩm hoặc chủ đề tìm đối tác một hàng, kèm từ khóa | Mỗi nhóm hàng có một đích phễu riêng |
| Đích của phễu | Mỗi nhóm hàng: link nhóm WhatsApp, Telegram, Zalo, Messenger hoặc website | Link WhatsApp phải bắt đầu `https://chat.whatsapp.com/`. Nhập số thành viên hằng tuần |
| Ngôn ngữ | Mã ngôn ngữ; tích **Đã được người thành thạo duyệt** khi văn phong đã được kiểm tra | Ngôn ngữ chưa duyệt chỉ ra bản nháp |
| Thông tin | Các câu ngắn, đúng sự thật, tích **Đã duyệt** | Là thông tin duy nhất Claude được dùng. Không có giá hay tồn kho trừ khi bạn ghi ở đây |
| Kênh | Dán URL nhóm hoặc fanpage, mỗi dòng một URL | Sau đó tự tham gia (Phần 5) |
| Giới hạn | **Thận trọng** trong 2 tuần đầu, sau đó **Bình thường** | Quy tắc an toàn luôn có hiệu lực |
| Lịch chạy | Chạy hằng ngày, lượt buổi chiều, giờ kiểm tra phản hồi | Theo múi giờ máy tính của bạn |

Bấm **Lưu** ở mỗi bước, rồi trong Claude Code gõ `/sync-control`. Claude ghi thay đổi vào workspace, kiểm tra hợp lệ và báo lỗi nếu có. Đầu trang hiện "Đã đồng bộ cấu hình" khi thành công.

### Tab Kênh
Mỗi nhóm hoặc fanpage một dòng. Giữ đúng các mục:
- **Trạng thái**:
  - *Chưa tham gia*: bạn chưa vào nhóm.
  - *Đang hoạt động*: đã vào nhóm và đã điền **Ngày tham gia**.
  - *Nghỉ tạm*: tạm nghỉ sau khi bị gỡ bài.
  - *Ngừng dùng*: không dùng nữa.
- **Bài chào hàng riêng** và **Liên kết trong bình luận**: theo quy tắc của nhóm. *Chưa rõ* được coi là *Không*.
- **Loại**: *Thảo luận*, *Bảng rao vặt* (mua bán số lượng lớn) hoặc *Fanpage*.

### Tab Duyệt bài
Hàng đợi trong ngày. Mỗi mục có ảnh xem trước kiểu Facebook, ý nghĩa bằng ngôn ngữ của bạn, và lý do Claude đề xuất.
- Bấm **Duyệt**, **Sửa** (ghi điều cần đổi) hoặc **Bỏ**.
- Sau đó nhắn Claude: **"đã duyệt như đã đánh dấu"**.
- Claude liệt kê lại các mục và hỏi xác nhận. Chỉ sau đó mới đăng.

### Tab Bảng theo dõi
- **Tổng quan**: kênh đang hoạt động, cuộc trò chuyện đang mở, số mục đã đăng, khách tiềm năng, phễu và danh sách mức sẵn sàng.
- **Cuộc trò chuyện**: giai đoạn của từng người, từ Gieo mầm đến Đã tham gia.
- **Khách tiềm năng**: người đã tương tác, kèm liên hệ chỉ khi họ tự cung cấp.
- **Bài đã đăng**, **Lượt chạy và quét**, **Sức khỏe** (XANH, VÀNG hoặc ĐỎ mỗi ngày, kèm sự cố).

### Tab Điều khiển
- **Tạm dừng tất cả** / **Bật lại**: mọi lượt chạy và đăng bài dừng khi tạm dừng.
- **Tạm dừng từng kênh**: nhóm đó bị bỏ qua.
- **Nhờ Claude chạy ngay**: để lại yêu cầu. Claude hỏi bạn trong chat trước khi chạy.
- **Ghi chú cho Claude**: sở thích và câu hỏi. Ghi chú không bao giờ khiến Claude tự đăng hay tham gia nhóm, và không đổi được quy tắc an toàn.

---

## Phần 5. Những việc chỉ bạn làm được

1. **Đăng nhập Facebook** trên trình duyệt mà Claude in Chrome dùng, và giữ đăng nhập. Claude không bao giờ đăng nhập, gõ mật khẩu hay giải CAPTCHA.
2. **Tham gia nhóm**, từng đợt vài nhóm mỗi tuần, rồi đặt kênh là **Đang hoạt động** kèm ngày tham gia. Thời gian làm quen tính từ ngày này: với mức Thận trọng, trong 14 ngày chỉ bình luận hữu ích, không liên kết, không bài chào hàng.
3. **Duyệt thông tin và ngôn ngữ** ở tab Thiết lập.
4. **Nhập số thành viên** của từng đích phễu hằng tuần. Đây là cách đo số người tham gia.
5. **Duyệt trong chat** mỗi ngày.

---

## Phần 6. Nhịp làm việc hằng ngày

| Khi nào | Bạn gõ | Việc xảy ra |
|---|---|---|
| Buổi sáng (mặc định 08:00) | `/social-seeding:daily-run` | Đồng bộ, kiểm tra sức khỏe tài khoản, quét nhóm, soạn nháp, kiểm duyệt và rà rủi ro. Hàng đợi hiện ở tab Duyệt bài |
| Sau khi xem | Đánh dấu trên trang và nhắn **"đã duyệt như đã đánh dấu"**, hoặc gõ `approve 1-5, 8; edit 3: ngắn hơn; drop 6` | Claude nhắc lại những gì sẽ đăng. Khi bạn đồng ý, `/post-approved` đăng, mỗi mục cách nhau ít nhất 10 phút, và ghi lại link |
| Buổi chiều (mặc định 16:00) | `/social-seeding:hot-replies` | Quét lần hai tìm bài mua và phản hồi mới |
| Mỗi giờ buổi tối, nếu đã cài | `/social-seeding:check-replies` | Bình luận và tin nhắn mới được soạn trả lời và báo cho bạn. Không gửi gì |
| Bất cứ lúc nào | `/social-seeding:health-check` | Sức khỏe tài khoản kèm bằng chứng |
| Sau khi sửa trên trang | `/social-seeding:sync-control` | Áp dụng thay đổi, báo ghi chú và yêu cầu |
| Thứ Sáu cách tuần | `/social-seeding:biweekly-report` | Báo cáo phễu, chất lượng, rủi ro và kênh kèm đề xuất |

Thường có thể bỏ tiền tố `social-seeding:` nếu không có skill nào khác trùng tên.

**Ngày chỉ soạn nháp:** thêm `--draft-only` vào lệnh chạy hằng ngày (ví dụ `/social-seeding:daily-run --draft-only`). Hàng đợi đó không thể đăng. Dùng cho ngày đầu, hoặc khi bạn chỉ muốn xem bản nháp mà không có rủi ro.

### Cách duyệt trong chat
- `approve 1-6, 9`: đăng mục 1 đến 6 và mục 9.
- `edit 4: <nội dung mới>`: Claude dùng đúng nội dung của bạn.
- `edit 4: ngắn hơn`: Claude viết lại và cho bạn xem trước.
- `drop 7`: không bao giờ đăng.
- **"đã duyệt như đã đánh dấu"**: dùng các đánh dấu ở tab Duyệt bài. Claude vẫn liệt kê lại và chờ bạn xác nhận.

---

## Phần 7. Sức khỏe tài khoản và an toàn

Claude xếp hạng tài khoản mỗi sáng:

| Mức | Ý nghĩa | Việc xảy ra |
|---|---|---|
| XANH | Không cảnh báo, bài hiển thị bình thường | Giới hạn bình thường |
| VÀNG | Có bài bị gỡ, kiểm tra hiển thị thất bại, hoặc nhiều bài chờ duyệt | Giới hạn giảm một nửa, không liên kết |
| ĐỎ | Bất kỳ cảnh báo, hạn chế, checkpoint hoặc khóa tính năng nào của Facebook | Dừng mọi thứ 72 giờ và báo bạn. **Bạn tự kiểm tra Account Status và Support Inbox.** Claude không bao giờ tự khôi phục tài khoản |

Các quy tắc an toàn cố định (trong `SAFETY.md`, không cài đặt nào đổi được):
1. Chỉ dùng danh tính thật, nêu rõ.
2. Không đăng gì khi chưa có sự đồng ý của bạn trong chat.
3. Claude không bao giờ đăng nhập, chỉ tham gia nhóm khi bạn yêu cầu.
4. Chỉ hành xử tuân thủ: giới hạn, nhịp đăng, độ liên quan. Không né tránh phát hiện.
5. Thông tin chỉ lấy từ tệp đã duyệt.
6. Không nhắn tin riêng cho người lạ.
7. Ở bảng rao vặt: chỉ trả lời người mua, tối đa 1 bài chào hàng mỗi nhóm mỗi ngày.
8. Không thu thập dữ liệu cá nhân ngoài những người đã tương tác với bạn.

---

## Phần 8. Xử lý sự cố

| Bạn thấy | Hãy làm |
|---|---|
| Trang báo "Đang chờ Claude xuất bản cấu hình" | Chạy `/social-seeding:publish-status` |
| Đầu trang báo "Lần đồng bộ gần nhất bị lỗi" | Mở tab Điều khiển để đọc lỗi, sửa ở tab Thiết lập rồi chạy lại `/sync-control`. Claude đã khôi phục cấu hình cũ nên không hỏng gì |
| `validate.py` báo lỗi | Mỗi dòng ghi rõ tệp và trường. Sửa trên trang hoặc trong `config/*.toml` |
| "No Chrome or Edge found" | Cài một trình duyệt, hoặc đặt biến `SSK_BROWSER` là đường dẫn .exe của trình duyệt |
| "cannot convert timezones" | `pip install tzdata` |
| Không tìm thấy skill | Mở Claude Code trong thư mục workspace (vì cài local), hoặc kiểm tra `claude plugin list` |
| Không có gì được đăng | Hàng đợi có phải chỉ nháp không? Ngôn ngữ chưa duyệt hay thông tin chưa duyệt? Workspace đang tạm dừng? Sức khỏe đang ĐỎ? |
| Bài chuyển sang "chờ phê duyệt" | Bình thường ở một số nhóm. Bài vẫn tính vào giới hạn; Claude ghi lại |
| Trang đăng nhập, CAPTCHA hoặc "tạm thời bị chặn" | Claude dừng. Bạn tự xử lý trên trình duyệt, rồi chạy `/social-seeding:health-check` |

---

## Phần 9. Cập nhật và sao lưu

- **Cập nhật plugin:** `claude plugin marketplace update social-seeding-kit`, rồi khởi động lại Claude Code. Dữ liệu workspace không bị đụng tới.
- **Sao lưu:** workspace là một repo git. Cấu hình và knowledge được theo dõi. Lượt chạy, cuộc trò chuyện, khách tiềm năng, báo cáo và nhật ký rủi ro được cố ý loại khỏi git vì chứa tên người, nên hãy tự sao chép các thư mục này nếu cần sao lưu.
- **Nhiều thương hiệu:** mỗi thương hiệu một thư mục workspace và một trung tâm điều khiển. Cài plugin với `--scope local` trong từng thư mục.
