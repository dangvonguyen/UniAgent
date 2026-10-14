# Nhật ký tune quy tắc mua sắm (từ 5 lên 9)

<!-- NINE_RULE_FINAL_START -->
> **Cập nhật 13/10/2026 · lượt mới 9 quy tắc × 8 hồ sơ.** Đọc [báo cáo lượt chín quy tắc](NINE_RULE_REVIEW_20261013.md) trước các kết quả 5 quy tắc phía dưới. Bốn quy tắc từng gọi là “ứng viên” nay đã được định nghĩa và chạy; các đoạn bên dưới mô tả lịch sử đến 11/10. Lượt GPT mới khớp 8/8 nhãn công khai, nhưng 43/72 kết quả quy tắc là `unknown` và cả tám hồ sơ `degraded`. Các nhãn `angenommen` là kết quả không có `fail`, chưa chứng minh mọi quy tắc đều đạt. Tập tám hồ sơ đã dùng để tune. Mã kiểm PDF tạo các lý do từ chối của 04, 06, 07; rule hợp đồng khung tạo lý do từ chối của 03. Đây là kết quả tập phát triển với cache quote; chưa xác nhận chạy lạnh trong 300 giây hoặc tập ẩn.

<!-- NINE_RULE_FINAL_END -->


**Phạm vi:** tám `beschaffungsantrag-01…08` công khai, hồ sơ xin mua trước đặt hàng. Báo cáo này phân biệt ba loại phép đo: chạy model mới, replay câu trả lời cũ qua mã mới, và audit PDF bằng mã. Các verdict `pass/fail/not_applicable` là nghiệp vụ; `unknown` là lỗi kỹ thuật hoặc thiếu căn cứ.

## Trình tự thử nghiệm

| Giai đoạn | Thao tác | Quan sát | Thay đổi hoặc quyết định |
| --- | --- | --- | --- |
| 08/10: rule hợp đồng khung | Truy xuất quote luật; GPT trên tám hồ sơ | 17 quote được giữ; case 03 bị đánh `fail` do email xin mua màn hình ngoài kênh hợp đồng, nhưng email chỉ nêu đề xuất. Case 08 ngoài danh sách `u.a.` không chứng minh không có hợp đồng. | Ràng buộc phạm vi theo nhóm hàng, phân biệt yêu cầu mua với đơn hàng đã đặt; không suy vắng mặt từ danh sách mở. |
| 09/10: rule báo giá | GPT tám hồ sơ với 4 quote, rồi lần chạy tái dùng digest | Case 02 áp nhầm ngoại lệ cho catering sang thiết bị điện tử; case 06 khai chỉ hai báo giá; case 08 có thư bổ sung cần đọc. | Gắn ngoại lệ với phạm vi mặt hàng/phương thức, xác minh số báo giá bằng PDF. Packet hiện có chưa xác lập ngoại lệ mua trực tiếp cho case 02. |
| 09/10: rule tính tiền và nhất quán | Audit PDF offline, GPT riêng cho rule 3/4 | Case 04: €2.220 + €180 = €2.400 nhưng đơn ghi €3.384. Case 07: giá M-5531 gốc €2.350 bị chép €3.243. Digest của rule 4 trả 0 quote. | Để mã tính và so sánh; phân biệt chẩn đoán dữ kiện với vi phạm nghĩa vụ luật. Không tự coi mọi khác biệt là `fail` policy. |
| 09–10/10: rule lựa chọn | Audit tám hồ sơ; GPT trên 01/07 | Audit thấy case 07 có giá bị chép sai. Digest mất 299,53 giây và hai quote từ một án lệ cũ nói về công bố tiêu chí, không xác lập nguyên tắc luôn chọn giá thấp nhất. | Không công nhận `pass` hoặc `fail` chỉ từ hai quote đó; giữ số liệu audit độc lập. |
| 10/10: sửa tầng bằng chứng | Bổ sung cổng quote luật/PDF, phạm vi sản phẩm, giai đoạn, ngoại lệ; sửa audit dùng giá gốc và hạn chế suy từ citation retry; chạy 8 test tổng hợp | Các trường hợp biến thể được kiểm có kết quả mong đợi. | Áp mã trong bản thử nghiệm, giữ lỗi nguồn là `unknown`; không nới gate để khớp nhãn công khai. |
| 10/10: matrix và replay | Matrix GPT 8×5 (43 request, 403,91 giây) rồi replay offline cùng câu trả lời qua mã mới | Matrix khớp 8/8 nhưng cả 8 degraded. Replay khớp 7/8, cả 8 còn `unknown`; case 03 chuyển thành chấp nhận tạm thời. | Đọc nhãn cùng căn cứ của từng rule, không dùng độ khớp nhãn matrix làm chứng nhận chất lượng lập luận. |
| 10/10: GPT giới hạn | Sáu cặp case–rule; 8 request, 183,89 giây; quote luật đã lưu | 1 verdict `fail` case 06 offers có 1 quote policy và 2 đoạn PDF; 5 `unknown` do gate, endpoint hoặc hết ngân sách. | Báo cáo đúng ở cấp cặp rule, không gọi đây là một lần chạy đủ tám hồ sơ. |
| 11/10: giai đoạn xin mua và tích hợp | Sửa cổng nhận quote `bestellen wollen` cho đề xuất xin mua; 9 test tổng hợp qua; chạy `predict.decide_case` offline với tám PDF và câu trả lời đã lưu | Khớp 8/8 nhãn công khai, nhưng 8/8 còn `unknown`. Case 03 thành `abgelehnt` không có audit fail; audit 04/06/07 giữ nguyên. | Tách nghĩa vụ đối với ý định đặt hàng khỏi nghĩa vụ chỉ đến hạn sau khi đã đặt. Không gọi đây là kết quả GPT mới hay kiểm tra hiệu năng 300 giây. |

Tài liệu gốc của các lượt thử, kể cả đường dẫn run cũ, nằm ở [historical-tuning-log.md](../evidence/historical-tuning-log.md). Bảng nhãn theo hồ sơ nằm ở [CASE_RESULTS.md](CASE_RESULTS.md).

## 1. `framework_contract_sourcing`

**Câu hỏi:** sản phẩm được xin mua có nằm trong phạm vi hợp đồng khung đã trích hay không; ở giai đoạn hiện tại có nghĩa vụ đặt qua nhà cung cấp/kênh đó hay ngoại lệ áp dụng không. Một liên kết webshop trong email xin mua là đề xuất, chưa tự chứng minh đã đặt hàng.

- **Thử ban đầu:** 17 quote từ policy digest, chạy tám hồ sơ. Model có lúc kết luận `fail` ở 03 từ email đề xuất; `not_applicable` ở 08 từ danh sách loại hàng không đầy đủ (`u.a.`). Các trường hợp này không đủ để khẳng định nghĩa vụ đã bị vi phạm hoặc vắng mặt.
- **Điều chỉnh:** tách bước nhận diện loại hàng, quote phạm vi, nghĩa vụ về kênh và giai đoạn; đòi trích đoạn PDF khớp thực tế. Nếu retry chỉ sửa citation thì không được lật verdict thiếu căn cứ mới. Pseudonymization của tên nhà cung cấp không tự là vi phạm.
- **Matrix GPT:** 03 `fail`, 05 `pass`, 04 `not_applicable`, 5 case `unknown`. Sau gate mới, replay chỉ còn 05 `pass`, 04 `not_applicable`, 6 `unknown`.
- **GPT cuối:** 03 `unknown` (`ordering-duty-not-shown-due-at-request-stage`), 05 và 08 `unknown` do endpoint hoặc citation retry. Không có `fail` framework được xác minh trong lượt cuối.
- **Sau sửa giai đoạn 11/10:** quote `bestellen wollen` cho biết nghĩa vụ liên quan đến ý định đặt hàng, nên cổng không còn đòi hóa đơn hoặc đơn đã thực hiện mới xét đề xuất. Kiểm tra tích hợp từ câu trả lời lưu cho case 03 `abgelehnt`, audit rỗng; báo cáo JSON chưa lưu verdict rule cụ thể. Lượt GPT cuối ở dòng trên là số đo **trước** sửa, không bị viết lại.
- **Nút thắt:** kiểm ngoại lệ và lập luận về kênh IT cho case 03 ở mức ngữ nghĩa, vì cổng mã xác minh nguồn/trình tự chứ không chứng minh toàn bộ lập luận. Danh sách mở không thể dùng làm chứng minh tuyệt đối rằng sản phẩm 08 không có hợp đồng khung.

## 2. `comparison_offers`

**Câu hỏi:** với phương thức và mặt hàng ghi trên hồ sơ, cần bao nhiêu báo giá, có ngoại lệ nào đúng phạm vi, và số báo giá thực tế là bao nhiêu. Chỉ đếm báo giá sau khi xác định quote nghĩa vụ và ngoại lệ.

- **Thử ban đầu:** 4 quote; chạy tám hồ sơ và một lượt tái dùng digest. Case 02 từng được cho `pass` nhờ quote ngoại lệ catering dưới €1.000 áp sang hàng điện tử; packet luật hiện tại không thiết lập kết luận đó. Case 08 có thư bổ sung các báo giá, không thể chỉ đọc email đầu.
- **Điều chỉnh:** cổng liên kết quote ngoại lệ với nhóm hàng và phương thức mua, audit đếm báo giá và checkbox hợp đồng khung. `unknown/policy_gap` được ghi khi packet chưa đủ, không tự chuyển thành `not_applicable`.
- **Matrix GPT:** 4 `pass` (01,04,05,07), 1 `fail` (06), 3 `unknown` (02,03,08). Replay qua mã mới giữ cùng phân bố này.
- **GPT cuối:** case 06 `fail` được xác minh: đơn nêu hai báo giá, quote quy định thông thường ba báo giá và ngoại lệ hợp đồng khung không được hồ sơ xác lập; 1 quote luật + 2 đoạn PDF. Case 03 `unknown` do `item-text-not-in-case:E2`, case 08 hết hạn mức trước lượt gọi.
- **Nút thắt:** tìm quy định mua trực tiếp đúng phạm vi cho 02; sửa trích đoạn của 03 và xử lý thư bổ sung ở 08. Cổng trích dẫn không thay thế việc đọc ngoại lệ chính xác.

## 3. `amount_calculation`

**Câu hỏi:** các dòng tiền và tổng tiền trong hồ sơ có khớp về đơn vị net/gross, thuế và giá ở báo giá hay không; nếu có nghĩa vụ định lượng trong policy thì so đúng cơ sở tính của quote.

- **Thử ban đầu:** audit PDF tám case cho một sai lệch, một trường hợp cần rà và sáu trường hợp kiểm được. GPT riêng với 4 quote từng trả 7 `pass`, 1 `unknown`; các `pass` đó chưa được coi là xác minh tuân thủ luật vì quote nghĩa vụ không khớp lập luận.
- **Điều chỉnh:** phép cộng/nhân và so giá do mã làm; không mặc định VAT 19% khi tài liệu không ghi; ghi `coverage_gap` khi bảng hoặc hóa đơn trích thiếu. Chỉ công nhận verdict nghiệp vụ khi có nghĩa vụ đúng phạm vi và fact PDF khớp.
- **Kết quả sau gate:** replay có 8/8 `unknown` ở verdict rule; audit riêng phát hiện case 04: €2.400 netto theo dòng và báo giá gốc, €3.384 trên đơn, lệch €984. Nhãn `abgelehnt` ở 04 trong replay đến từ audit, không từ một `fail` GPT đã xác minh của rule này.
- **Nút thắt:** chứng minh nghĩa vụ policy áp dụng ở giai đoạn xin mua; nhiều `pass` cũ mới chỉ nói phép tính đúng. Cần kiểm các hóa đơn một phần ở 08 nếu dùng chúng để so tổng.

## 4. `document_consistency`

**Câu hỏi:** các tài liệu của cùng yêu cầu mua có tự mâu thuẫn về mã báo giá, mặt hàng, tổng tiền hoặc giá được chép trong biên bản hay không.

- **Thử ban đầu:** audit offline v1/v2 trên tám hồ sơ thấy case 04 và 07 có discrepancy; case 03 thiếu tài liệu đối chiếu. Lượt GPT resolve policy cho rule này trả **0 quote**, nên đã dừng các lượt case GPT tốn phí.
- **Điều chỉnh:** đối chiếu báo giá gốc, đơn và biên bản bằng mã, ghép mã báo giá xuống dòng; kiểm từ nguồn gốc để tránh tin giá chép trong biên bản. Không chạy `pdftotext` hai lần khi text đã có.
- **Kết quả sau gate:** replay 8/8 `unknown` cho verdict GPT của rule này. Audit case 07 xác định báo giá M-5531 gốc €2.350 và biên bản €3.243; case 04 có tổng tiền đơn khác báo giá. Case 03 là `coverage_gap`, không phải hồ sơ “nhất quán”.
- **Nút thắt:** 0 quote luật nghĩa vụ áp dụng; audit tài liệu là bằng chứng có ích nhưng cần xác định rõ điều kiện nào đủ để thành `fail` ở cấp hồ sơ. Audit 04/07 hiện có đường đánh dấu lỗi tự mâu thuẫn đã định nghĩa trong pilot, và phải được đánh giá riêng với verdict model.

## 5. `award_selection`

**Câu hỏi:** nhà cung cấp được đề xuất có phù hợp tiêu chí ghi trong tài liệu và quy định áp dụng ở giai đoạn này không; dữ liệu giá phải lấy từ báo giá gốc khi biên bản chép khác.

- **Thử ban đầu:** audit có 1 mâu thuẫn, 3 trường hợp nhất quán theo tiêu chí đã nêu, 4 hồ sơ không có biên bản chọn. GPT riêng ở 01 trả `pass`, 07 trả `rule_error`. Hai quote được digest chọn từ cùng án lệ về **công bố tiêu chí**, không chứng minh nghĩa vụ **chọn thấp nhất**; một lượt digest mất 299,53 giây.
- **Điều chỉnh:** không lấy `pass` chỉ vì giá được chọn thấp nhất; không lấy `fail` vì một giá bị chép sai khi chưa rõ căn cứ nghĩa vụ chọn nhà cung cấp. Audit giá gốc tách khỏi kết luận luật.
- **Matrix GPT:** 3 `unknown`, 5 `not_applicable`; replay sau gate: 4 `unknown`, 4 `not_applicable`.
- **Nút thắt:** quote đúng về tiêu chí chọn và ngoại lệ chưa có. `not_applicable` chỉ vì thiếu biên bản có thể bỏ sót đề xuất chọn thể hiện qua email. Rà thời gian digest trong hạn 300 giây toàn hồ sơ.

## Phạm vi kiểm chứng và việc còn mở

- Ba kết quả tổng hợp nằm trong [README chính](../README.md); [CASE_RESULTS.md](CASE_RESULTS.md) cho biết nguyên nhân theo case. Các báo cáo máy đọc được ở `evidence/matrix/`, `evidence/offline/`, `evidence/final/`.
- Chín test tổng hợp sau sửa 11/10 kiểm các biến thể về giá, số báo giá, exception, source span và giai đoạn. Chúng không chứng minh recall của retrieval hoặc độ chính xác tập ẩn.
- Cần rà nguồn luật đúng phạm vi rule 2–5, xử lý thiếu quote và endpoint gián đoạn, đo đường chạy lạnh trọn pipeline trong 300 giây/hồ sơ. Chưa có số đo của pipeline chính với Reflect trên procurement.

## Cập nhật lượt chín quy tắc ngày 13/10/2026

Bốn nhóm bổ sung (thẩm quyền đặt hàng, phân loại tài sản, thiết bị nghiên cứu đặc biệt, nhập khẩu ngoài EU) đã được định nghĩa và chạy cùng năm nhóm cũ. Lượt chạy dùng `gpt-oss-20b` và các gói quote luật đã chuẩn bị trước, trên tám hồ sơ công khai từng được dùng để tune. Mỗi hồ sơ có chín kết quả rule. Nhãn cuối khớp 8/8 nhãn công khai, nhưng đây là **kết quả tập phát triển**, không phải đánh giá trên tập ẩn. Cả tám hồ sơ `degraded`; trong 72 kết quả rule có 43 `unknown`, 19 `not_applicable`, 7 `pass`, 3 `fail`.

| Rule | Đã làm và tín hiệu trên tám hồ sơ | Giới hạn hiện tại |
| --- | --- | --- |
| `framework_contract_sourcing` | Sửa giai đoạn xin mua, quote phạm vi hàng và kênh WPS; case 03 `fail` với đề xuất mua màn hình ngoài hợp đồng. | Kết luận `pass` ở 02/08 dựa vào danh sách `u.a.` mở nên quá chắc; 05 còn vấn đề tên trường/đối tác đã thay. |
| `comparison_offers` | Nối ngoại lệ với loại hàng; case 06 `fail` vì hai báo giá thay vì ba, kèm audit hồ sơ. | 02 thiếu quote mua trực tiếp đúng phạm vi; `fail` phụ ở 03 còn cần rà. |
| `amount_calculation` | Mã đối chiếu số tiền bắt 04: 2.400 so với 3.384 EUR net. | Kết quả LLM chủ yếu `unknown`; quote ngưỡng không tự tạo nghĩa vụ số học. |
| `document_consistency` | Mã đối chiếu báo giá gốc và biên bản bắt 07: 2.350 bị chép thành 3.243 EUR net. | Digest không có quote nghĩa vụ; đây là audit tài liệu. |
| `award_selection` | Cổng từ chối quote về công bố tiêu chí khi model suy phải chọn giá thấp nhất. | 8/8 `unknown`; thiếu nguồn nghĩa vụ thích hợp. |
| `request_and_order_authority` | 4 `pass`, 4 `unknown`; quote về thẩm quyền đúng chủ đề. | Cần củng cố liên kết nghĩa vụ với chữ ký và giai đoạn. |
| `asset_classification` | Thêm kiểm tra `Verbrauchsmaterial`/`GWG`/`Anlage`. | 8 `unknown`; nguồn có ngưỡng cũ/mới xung đột, thiếu metadata hiệu lực. |
| `special_research_equipment_procedure` | Quote về thủ tục thiết bị nghiên cứu đã được tìm đúng chủ đề. | 8 `not_applicable`; chưa có hồ sơ dương tính để kiểm độ nhạy. |
| `non_eu_import_procurement` | Quote về nhập khẩu ngoài EU đã được tìm đúng chủ đề. | 8 `not_applicable`; địa chỉ nhà cung cấp ở EU không tự chứng minh xuất xứ hàng. |

Nhãn từ chối của 04 và 07 đến từ audit PDF bằng mã, của 06 từ rule báo giá và audit, của 03 từ rule hợp đồng khung. Bốn hồ sơ được chấp nhận vì không có `fail`, trong khi vẫn còn `unknown`. Dữ liệu thô của lượt chạy được giữ cục bộ tại `uniagent/runs/procurement/nine-final-20261013-120322/`; cache quote tại `uniagent/runs/procurement/nine-persistent-cache/`. Chúng không nằm trong phần mã/tài liệu đưa lên Git.

Thời gian xử lý chậm nhất một hồ sơ là khoảng 172,5 giây khi dùng cache; lượt chạy lạnh bao gồm dựng chỉ mục và chọn quote chưa được xác nhận trong hạn 300 giây. Việc tune trên tám hồ sơ công khai có nguy cơ khớp quá mức; các rule mới chưa có case dương tính và cả chín rule chưa được kiểm trên tập ẩn.

## Kiểm tra image tích hợp ngày 14/10/2026

Image build thành công từ `uniagent/` ở gốc. Kiểm tra khi tắt mạng xác nhận
pipeline import được đủ 9 quy tắc mua sắm và PyTerrier khởi động bằng Java helper
đã lưu trong image. Lượt kiểm này không gọi GPT và không chạy 8 hồ sơ.
Kết quả 8/8 đã báo cáo ở trên thuộc lượt chạy tập phát triển trước các sửa đổi
tích hợp mới; chưa được xác nhận lại bằng image này.
