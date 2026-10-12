# Procurement: kết quả theo từng hồ sơ

Các phép đo dưới đây **khác nhau**: `matrix` là lượt GPT cũ trên 8 hồ sơ × 5 rule; `offline replay` chạy lại câu trả lời đã lưu qua cổng mã lúc 10/10, **không gọi GPT**; lượt GPT cuối chỉ gọi sáu cặp hồ sơ–rule. Ngày 11/10, kiểm tra tích hợp `decide_case` dùng cùng câu trả lời cũ với cổng giai đoạn đã sửa. Vì thế không có một bảng nhãn *8/8 từ GPT cuối*. Nhãn BTC ở đây là nhãn công khai dùng để đối chiếu sau khi dự đoán.

Ký hiệu theo thứ tự rule `framework / offers / amount / consistency / award`: `P` = pass, `F` = fail, `N` = not_applicable, `U` = unknown kỹ thuật. Audit PDF có thể thêm `fail` độc lập với năm verdict model. `unknown` không phải verdict nghiệp vụ và hiện có thể dẫn tới nhãn `angenommen` tạm thời nếu không có `fail` nào khác.

| Case | BTC | Matrix GPT cũ | Offline replay mã mới | 5 rule trong replay | Audit dẫn đến từ chối / điểm chưa xong | GPT cuối có giới hạn |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | angenommen | angenommen | angenommen (4 U) | U / P / U / U / U | Offers `pass`; các rule khác chưa đủ bằng chứng; không có audit fail. | Không gọi lại. |
| 02 | angenommen | angenommen | angenommen (4 U) | U / U / U / U / N | Rule offers thiếu quote đúng phạm vi cho phương thức mua trực tiếp; chưa xác minh các rule còn lại. | Không gọi lại vì cùng packet quote không thể bổ sung điều luật. |
| 03 | abgelehnt | abgelehnt | **angenommen tạm thời (sai nhãn công khai; 4 U)** | U / U / U / U / N | Email đề xuất mua màn hình từ webshop chưa chứng minh đã đặt hàng hoặc nghĩa vụ đặt hàng đã đến hạn; không có audit fail. | Framework `U` do gate giai đoạn; offers `U` do excerpt mặt hàng không khớp PDF. Chưa xác minh được `fail`. |
| 04 | abgelehnt | abgelehnt | abgelehnt (3 U) | N / P / U / U / U | Audit: tổng hai dòng €2.400 netto nhưng đơn ghi €3.384, lệch €984. | Không gọi lại. |
| 05 | angenommen | angenommen | angenommen (2 U) | P / P / U / U / N | Framework và offers `pass` từ câu trả lời cũ qua replay; rule 3/4 còn unknown. | Framework `U`: lượt sửa citation bị endpoint ngắt, **không kế thừa `pass` của replay**. |
| 06 | abgelehnt | abgelehnt | abgelehnt (4 U) | U / F / U / U / U | Hồ sơ nêu 2 báo giá so với nghĩa vụ thông thường 3; audit ghi cùng thiếu hụt với kiểm tra ngoại lệ. | Offers `fail` với **1 quote policy + 2 đoạn PDF xác minh**. |
| 07 | abgelehnt | abgelehnt | abgelehnt (4 U) | U / P / U / U / U | Audit đối chiếu báo giá gốc M-5531 €2.350 với giá bị chép €3.243 trong biên bản. | Không gọi lại. |
| 08 | angenommen | angenommen | angenommen (4 U) | U / U / U / U / N | Không có audit fail; framework/offers chưa được xác minh đầy đủ, cần đọc thư bổ sung báo giá. | Framework `U` do endpoint ngắt; offers `U` vì hết giới hạn request **trước khi gọi**. |

**Đếm nhãn:** matrix cũ khớp 8/8 nhưng tất cả hồ sơ degraded. Offline replay khớp **7/8** và cả 8 còn unknown. Lượt GPT cuối dùng 8 request trong 183,89 giây, chỉ **1/6 cặp rule–case có verdict được xác minh** (`fail` ở case 06); năm cặp còn lại là lỗi kỹ thuật hoặc thiếu căn cứ, không dùng để tính accuracy tám hồ sơ.

## Tích hợp `decide_case` sau sửa cổng giai đoạn, 11/10

Đã chạy đúng hàm `predict.decide_case()` với tám thư mục PDF thật; `check_case` lấy câu trả lời GPT và quote từ matrix đã lưu, qua cổng mã hiện tại. Không gọi GPT, không truy xuất corpus hay chạy digest lại. Báo cáo [decide-case-offline.json](../evidence/integration/decide-case-offline.json) chỉ lưu nhãn, audit `fail` và ID các rule còn lỗi kỹ thuật; nó **không lưu verdict/lý do từng rule**. Case 03 đổi nhãn do sửa cổng giai đoạn là suy ra từ mã và replay trước đó, chưa phải một lượt suy luận mới của model.

| Case | Nhãn BTC | `decide_case` 11/10 | Audit `fail` | Rule còn `unknown` |
| --- | --- | --- | --- | ---: |
| 01 | angenommen | angenommen | — | 4 |
| 02 | angenommen | angenommen | — | 4 |
| 03 | abgelehnt | abgelehnt | — | 3 |
| 04 | abgelehnt | abgelehnt | `form_total` | 3 |
| 05 | angenommen | angenommen | — | 2 |
| 06 | abgelehnt | abgelehnt | `declared_method_missing_offers` | 4 |
| 07 | abgelehnt | abgelehnt | `offer_vs_award_note` | 4 |
| 08 | angenommen | angenommen | — | 4 |

**Đọc kết quả:** 8/8 khớp nhãn công khai trên tập đã dùng để tune; 8/8 còn lỗi kỹ thuật ở ít nhất một rule. Ba đường audit từ chối 04/06/07 khớp báo cáo trước. Riêng 03 không có audit `fail`; ở replay cũ framework bị chặn chỉ bởi `ordering-duty-not-shown-due-at-request-stage`, và bản sửa cho phép xét quote `bestellen wollen` ở giai đoạn đề xuất. Cổng phạm vi/trích dẫn vẫn phải qua, nhưng báo cáo tích hợp hiện không xuất trực tiếp verdict và ngoại lệ cho rule 1; cần kiểm tra phần đó trước khi coi lập luận case 03 là đã chứng minh trọn vẹn.

## Nguồn và cách đọc

- Lịch sử tune và trạng thái từng rule: [PROCUREMENT_TUNING.md](PROCUREMENT_TUNING.md).
- Báo cáo 8 × 5 cũ: [matrix-report.json](../evidence/matrix/matrix-report.json); trace tương ứng nằm cùng thư mục.
- Verdict từng rule sau replay và audit từng case: [replay-report.json](../evidence/offline/replay-report.json).
- Sáu cặp GPT mới, thời gian, nguồn đã xác minh và lỗi: [final-report.json](../evidence/final/final-report.json), [trace](../evidence/final/run-trace.jsonl.log.gz), [stdout](../evidence/final/stdout.log).

Kết quả công khai là tập phát triển đã dùng để tune. Chưa có phép đo trên tập ẩn, lượt chạy lạnh đầy đủ trong 300 giây/hồ sơ hoặc kiểm tra tích hợp với Reflect trong pipeline chính.
