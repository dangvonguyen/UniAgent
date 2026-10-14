# Báo cáo thử nghiệm pipeline xét hồ sơ mua sắm nội bộ

<!-- PROCUREMENT_NINE_RULES_START -->
> **Cập nhật 13/10/2026:** Đã định nghĩa và chạy 9 quy tắc trên 8 hồ sơ công khai. Nhãn cuối khớp 8/8 trên tập phát triển, nhưng 43/72 kết quả quy tắc là `unknown`; cả tám hồ sơ còn trạng thái `degraded`. Xem [lịch sử tune](docs/PROCUREMENT_TUNING.md#cập-nhật-lượt-chín-quy-tắc-ngày-13102026). Các mô tả năm quy tắc phía dưới là lịch sử giai đoạn trước.

<!-- PROCUREMENT_NINE_RULES_END -->


**UniAgent Task 2 · 8 hồ sơ công khai · cập nhật 11/10/2026**

## Mục tiêu và phạm vi

Thử nghiệm năm nhóm kiểm tra cho hồ sơ **xin mua trước khi đặt hàng**: hợp đồng khung, số báo giá, số tiền, tính nhất quán giữa tài liệu và lựa chọn nhà cung cấp. Mỗi rule đọc quote luật từ corpus và dữ kiện PDF; mã xác minh trích dẫn, tính toán và đối chiếu được giữ riêng trong audit. Đây là snapshot thử nghiệm trên tám hồ sơ công khai, chưa phải kết quả trên tập ẩn hoặc một lượt chạy lạnh toàn pipeline.

Sau khi rà các trang mua sắm trong corpus, báo cáo [trạng thái bàn giao](docs/HANDOFF_STATUS.md#rà-phạm-vi-quy-tắc-trên-corpus-mua-sắm) liệt kê **bốn ứng viên rule bổ sung** về thẩm quyền, phân loại tài sản, thiết bị nghiên cứu đặc biệt và hàng nhập ngoài EU. Chúng chưa được triển khai hoặc kiểm thử và không nằm trong kết quả 8/8; chưa xác nhận bộ rule bao phủ toàn bộ nghĩa vụ mua sắm.

Trạng thái nghiệp vụ của rule là `pass`, `fail`, `not_applicable`. `unknown`/`rule_error` trong báo cáo là **lỗi kỹ thuật hoặc thiếu căn cứ**, không phải verdict thứ tư. Nếu không có `fail`, nhãn hồ sơ hiện có thể là `angenommen` dù còn rule `unknown`; bảng kết quả ghi rõ các nhãn như vậy là tạm thời.

## Kết quả đo được

| Phép đo | Cách chạy | Kết quả | Giới hạn diễn giải |
| --- | --- | --- | --- |
| Matrix GPT 8 × 5 | `gpt-oss-20b`, tái dùng policy digest đã lưu; tối đa 48 request | Khớp **8/8** nhãn công khai; 43 request, 403,91 giây toàn lượt; **8/8** hồ sơ `degraded` | Đây là tập đã dùng để phát triển. Nhãn đúng không bảo đảm lập luận từng rule đúng. Không bao gồm thời gian dựng corpus/digest từ đầu. |
| Replay offline sau cổng bằng chứng mới | Dùng lại câu trả lời GPT của matrix và PDF thật; **không gọi GPT** | Khớp **7/8**; **8/8** hồ sơ còn ít nhất một `unknown`; case 03 chuyển thành `angenommen` tạm thời | Đo tác động của mã mới trên câu trả lời đã lưu, không đo chất lượng một lượt model mới. |
| GPT kiểm tra cuối theo cặp | `gpt-oss-20b`, sáu cặp hồ sơ–rule được chọn; quote luật đã lưu | 8/8 request cho phép trong 183,89 giây; **1/6** cặp có verdict được xác minh (`comparison_offers`, case 06: `fail`); **5/6** cặp `unknown` | Không phải lượt 8 × 5 mới, không tạo được số đo accuracy theo tám hồ sơ, không đo khởi động lạnh. |
| Kiểm tra tích hợp `decide_case` sau sửa giai đoạn (11/10) | Tám PDF thật, câu trả lời GPT và quote luật đã lưu; **không gọi GPT** | Khớp **8/8** nhãn công khai; **8/8** vẫn có `unknown`. Case 03 đổi thành `abgelehnt`; audit fail 04/06/07 giữ nguyên | Đo cổng giai đoạn, audit và phép gộp trên câu trả lời cũ. Không chứng minh lượt model mới, retrieval mới hoặc chạy lạnh dưới 300 giây. |

Chi tiết từng hồ sơ và trạng thái từng rule ở [CASE_RESULTS.md](docs/CASE_RESULTS.md). Nguyên nhân từng cặp ở lượt cuối nằm trong [FINAL_REVIEW.md](docs/FINAL_REVIEW.md). [PROCUREMENT_TUNING.md](docs/PROCUREMENT_TUNING.md) ghi quá trình thay đổi theo thời gian và theo rule.

**Quyết định bàn giao:** [HANDOFF_STATUS.md](docs/HANDOFF_STATUS.md) tổng hợp phần đã tune, vấn đề còn mở và điều kiện cần đạt trước khi tích hợp vào pipeline chính.

## Quá trình thực hiện

1. **Xây năm rule và thử riêng từng rule (08–09/10).** Giữ cách lấy quote từ retrieval/digest của pipeline nền. Rule hợp đồng khung và báo giá chạy GPT trên tám hồ sơ; số tiền, nhất quán tài liệu và lựa chọn nhà cung cấp có audit offline trước khi thử model. Bước này bộc lộ lỗi quote thiếu phạm vi, nhầm ngoại lệ của mặt hàng khác, suy từ email xin mua thành đơn hàng đã thực hiện, và dùng quy định công bố tiêu chí để kết luận phải chọn giá thấp nhất.
2. **Thêm kiểm tra bằng mã (09–10/10).** So dòng hàng với tổng tiền, đối chiếu báo giá gốc với đơn và biên bản, kiểm số báo giá cùng phương thức mua và ngoại lệ. Cổng nguồn buộc trích đoạn policy và PDF có thật, liên kết loại hàng, giai đoạn và nghĩa vụ trước khi công nhận verdict; lỗi nguồn được giữ là `unknown` thay vì biến thành một `pass` hay `fail` không có căn cứ. Tám test biến thể tổng hợp của gói `onepass` đã pass; chúng không thay thế kiểm thử trên PDF đa dạng.
3. **Chạy matrix, replay rồi GPT giới hạn (10/10).** Matrix cung cấp câu trả lời đã lưu; replay cho thấy cổng mới bác nhiều lập luận cũ và nhãn case 03 không còn được chứng minh. Lượt GPT cuối tập trung vào các cặp còn tranh cãi trong giới hạn request, và phân biệt được lỗi bằng chứng, lỗi endpoint và hết ngân sách thử nghiệm.
4. **Chốt giai đoạn xin mua và kiểm tra tích hợp offline (11/10).** Quote `bestellen wollen` nói tới ý định đặt hàng, nên cổng cho phép xét đề xuất xin mua ngay ở giai đoạn này; nghĩa vụ chỉ phát sinh sau khi đặt hàng vẫn bị chặn. Chín test tổng hợp qua. Chạy `predict.decide_case()` trên tám PDF với câu trả lời đã lưu cho 8/8 nhãn công khai, nhưng cả tám hồ sơ còn ít nhất một rule `unknown`. Audit của 04/06/07 được giữ nguyên.

Quá trình từng rule, các run và kết quả trước/sau nằm trong [nhật ký tune](docs/PROCUREMENT_TUNING.md). Bản ghi gốc của lịch sử chạy được giữ tại [historical-tuning-log.md](evidence/historical-tuning-log.md); các đường dẫn run cũ trong bản ghi này tương ứng với thư mục `runs/procurement` của pilot, không phải toàn bộ đều được đóng gói ở đây.

## Kết luận theo rule

| Rule | Kết quả đáng tin cậy hiện có | Vấn đề còn lại |
| --- | --- | --- |
| `framework_contract_sourcing` | Cổng giai đoạn nay nhận câu luật `bestellen wollen` ở bước xin mua; trên replay cũ case 03 đổi sang từ chối khi không có audit fail. | Chưa có lượt GPT mới xác nhận tính ổn định; cổng chỉ kiểm thời điểm và trích dẫn, không chứng minh mọi ngoại lệ đều đã được xét đúng. Danh sách hợp đồng khung mở (`u.a.`) không chứng minh vắng mặt. |
| `comparison_offers` | Case 06 có `fail` được xác minh trong GPT cuối bằng 1 quote luật và 2 đoạn PDF. | Case 02 thiếu quote áp dụng cho mua trực tiếp hàng điện tử; case 03/08 còn trục trặc nguồn và trích đoạn. |
| `amount_calculation` | Audit bằng mã phát hiện case 04: tổng vị trí €2.400 netto, đơn ghi €3.384. | Phép tính đúng không tự chứng minh đã tuân thủ một nghĩa vụ luật; cần quote đúng phạm vi cho verdict nghiệp vụ. |
| `document_consistency` | Audit đối chiếu case 04 và 07; case 07 chép giá báo giá M-5531 €2.350 thành €3.243 trong biên bản. | Digest trả **0 quote nghĩa vụ** cho rule này; chưa thể lấy chẩn đoán tài liệu làm kết luận luật một cách tổng quát. |
| `award_selection` | Audit mô tả giá và tiêu chí ghi trong hồ sơ. | Hai quote tìm thấy nói về công bố tiêu chí, không xác lập nghĩa vụ chọn giá thấp nhất; chưa xác minh được `pass/fail` từ rule GPT. |

## Giới hạn của kết quả

- Tám hồ sơ và nhãn công khai đã được dùng khi phát triển. **8/8 của matrix là độ khớp trên tập phát triển**, không dự báo kết quả tập ẩn.
- Quote luật của lượt matrix và GPT cuối được lấy từ digest lưu sẵn. Chưa đo trọn retrieval, khởi động lạnh, Reflect và năm rule trong một lượt dưới hạn **300 giây/hồ sơ**. Một lần digest rule 5 riêng từng mất 299,53 giây.
- `unknown` có thể rơi vào nhãn hồ sơ `angenommen` theo phép gộp hiện tại. Bản replay trước khi sửa giai đoạn cho thấy rủi ro đó ở case 03; sau sửa, case 03 ra `abgelehnt` từ câu trả lời cũ. Bốn hồ sơ được nhận vẫn là nhãn tạm thời khi còn rule chưa kiểm xong.
- Snapshot này không kèm PDF, corpus retrieval, model cache hoặc image Docker; các lệnh tái chạy cần tài nguyên đầu vào tương ứng. Gói bàn giao gồm danh sách stopwords tiếng Đức và thông báo nguồn đi kèm để import mã retrieval không phụ thuộc resource của image. Không có đánh giá trên ba chủ đề Task 2 như một hệ thống hoàn chỉnh.

## Dữ liệu và mã đi kèm

| Vị trí | Nội dung |
| --- | --- |
| [`docs/PROCUREMENT_TUNING.md`](docs/PROCUREMENT_TUNING.md) | Nhật ký diễn biến và trạng thái của từng rule. |
| [`docs/HANDOFF_STATUS.md`](docs/HANDOFF_STATUS.md) | Quyết định bàn giao, phần đã tune, phần còn mở và điều kiện tích hợp. |
| [`docs/CASE_RESULTS.md`](docs/CASE_RESULTS.md) | Bảng tám hồ sơ và nguyên nhân nhãn. |
| [`docs/FINAL_REVIEW.md`](docs/FINAL_REVIEW.md) | Sáu cặp GPT cuối, lỗi và bằng chứng. |
| [`evidence/matrix/matrix-report.json`](evidence/matrix/matrix-report.json) | Lượt GPT 8 × 5 trước khi áp cổng mới. |
| [`evidence/offline/replay-report.json`](evidence/offline/replay-report.json) | Verdict và audit khi replay câu trả lời cũ qua mã mới. |
| [`evidence/final/final-report.json`](evidence/final/final-report.json) | Lượt GPT giới hạn; trace và stdout ở cùng thư mục. |
| [`evidence/integration/decide-case-offline.json`](evidence/integration/decide-case-offline.json) | `decide_case` trên tám PDF và câu trả lời lưu: nhãn, audit và số rule còn lỗi kỹ thuật. |
| `uniagent/`, `tools/` | Snapshot mã thử nghiệm, test và công cụ replay; `tools/manifest.json` ghi hash các file nguồn đã thay đổi. |

**Trạng thái mã:** thay đổi được giữ trong repo thử nghiệm độc lập; chưa kiểm chứng tích hợp vào pipeline chính với retrieval, Reflect và cấu hình chạy thật. Đây là ranh giới đo được của kết quả trên.
