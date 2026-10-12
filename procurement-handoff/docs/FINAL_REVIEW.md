# Lượt GPT cuối: kiểm tra bằng chứng theo cặp hồ sơ–rule

Ngày 10/10/2026, `gpt-oss-20b` được gọi trên sáu cặp đã chọn với quote luật lấy từ policy digest lưu trước đó. Giới hạn thử nghiệm là **8 request**, sử dụng hết trong **183,89 giây**. Lượt này không dựng lại index/digest, không chạy đủ 8 hồ sơ × 5 rule và không xác nhận thời gian khởi động lạnh.

| Hồ sơ | Rule | Verdict sau gate | Policy được xác minh | PDF được xác minh | Diễn giải |
| --- | --- | --- | ---: | ---: | --- |
| 03 | `framework_contract_sourcing` | `unknown` | 0 | 0 | `ordering-duty-not-shown-due-at-request-stage`: quote nói về cách đặt hàng; email trong hồ sơ mới đề xuất mua, chưa chứng minh đơn đã đặt hoặc nghĩa vụ đã đến hạn. Retry không giải quyết được. |
| 03 | `comparison_offers` | `unknown` | 0 | 0 | `item-text-not-in-case:E2`: đoạn mô tả mặt hàng dùng để liên kết phạm vi không khớp PDF sau retry. |
| 05 | `framework_contract_sourcing` | `unknown` | 0 | 0 | Lượt đầu không qua cổng trích dẫn; endpoint ngắt kết nối khi thử sửa. Không được tính là `pass` từ replay cũ. |
| 06 | `comparison_offers` | **`fail`** | **1** | **2** | Policy nêu thông thường cần ba báo giá trừ trường hợp hợp đồng khung; đơn khai hai báo giá, hồ sơ có hai nhà cung cấp, không xác lập ngoại lệ hợp đồng khung. |
| 08 | `framework_contract_sourcing` | `unknown` | 0 | 0 | Endpoint ngắt trước khi có câu trả lời hợp lệ. |
| 08 | `comparison_offers` | `unknown` | 0 | 0 | Hết ngân sách tám request trước khi gọi, không có đánh giá model mới. |

**Kết quả:** chỉ **1/6 cặp** có verdict với quote luật và đoạn PDF đã xác minh; 5/6 cặp còn `unknown`. Đây là tỷ lệ hoàn tất của phép thử có giới hạn, không phải độ chính xác phân loại sáu cặp hay tám hồ sơ. Lỗi case 03 là căn cứ và giai đoạn; case 05/08 framework là lỗi endpoint; 08 offers chưa được gọi. Không thể gộp chúng thành một nguyên nhân chung.

Replay offline ngay trước lượt này khớp **7/8 nhãn công khai**, nhưng replay không gọi GPT và cả 8 hồ sơ còn rule `unknown`. Việc case 03 thành `angenommen` trong replay là nhãn tạm thời do chưa có `fail` qua gate, khác nhãn công khai `abgelehnt`. Không nới điều kiện bằng chứng chỉ để làm nhãn công khai khớp lại.

**Giới hạn còn lại:** rule 3 cần quote nghĩa vụ thích hợp để công nhận `pass/fail`, rule 4 tìm được 0 quote, hai quote của rule 5 chỉ về công bố tiêu chí. Audit số học và đối chiếu tài liệu vẫn có ích nhưng không thay thế căn cứ luật đúng phạm vi. Lượt này không kiểm tốc độ đầy đủ dưới 300 giây/hồ sơ, retrieval mới hoặc Reflect.

Số liệu gốc: [final-report.json](../evidence/final/final-report.json), [trace](../evidence/final/run-trace.jsonl.log.gz) và [stdout](../evidence/final/stdout.log).

## Kiểm tra tiếp theo, 11/10/2026

Sau lượt GPT trên, cổng giai đoạn được sửa để nhận một nghĩa vụ nêu rõ ý định `bestellen wollen` khi xét hồ sơ xin mua. Chín test tổng hợp qua. Một lượt **offline** đã chạy `predict.decide_case()` trên tám PDF bằng câu trả lời GPT lưu từ matrix: nhãn khớp 8/8 công khai, case 03 đổi sang `abgelehnt`, audit fail của 04/06/07 không thay đổi, và cả tám hồ sơ vẫn có ít nhất một rule `unknown`. Xem [báo cáo tích hợp](../evidence/integration/decide-case-offline.json) và [bảng từng case](CASE_RESULTS.md). Số liệu 1/6 và lý do `unknown` của lượt GPT ngày 10/10 trong bảng trên là lịch sử của **mã cũ**, không được thay bằng kết quả offline này.
