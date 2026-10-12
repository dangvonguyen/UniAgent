# Trạng thái bàn giao: pilot xét hồ sơ mua sắm

**11/10/2026 · Phạm vi: 8 hồ sơ mua sắm công khai · Trạng thái: pilot để review và tích hợp có điều kiện.** Đây là mã thử nghiệm độc lập; chưa merge vào pipeline chính có Reflect, chưa đo tập ẩn và chưa xác nhận lượt chạy lạnh trong 300 giây/hồ sơ.

Hạn mức endpoint GPT dùng chung của nhóm đã hết trước lượt kiểm tra dự kiến sau bản sửa giai đoạn. Vì vậy, **không có kết quả GPT mới với mã cuối**. Bằng chứng cuối cùng của bản này là test tổng hợp và replay offline trên PDF thật với câu trả lời GPT đã lưu; không trình bày replay như một lượt chạy model mới.

## Kết quả được phép báo cáo

| Phép đo | Kết quả | Cách hiểu |
| --- | --- | --- |
| Matrix GPT cũ, 8 × 5 | Khớp 8/8 nhãn công khai; 8/8 hồ sơ degraded | Các case này đã được dùng để tune; một nhãn đúng không xác minh lý do của mọi rule. |
| GPT cuối có giới hạn, trước sửa giai đoạn | 1/6 cặp rule–case hoàn tất với bằng chứng qua gate; 5/6 unknown | Chỉ gọi sáu cặp đã chọn, không phải chạy toàn pipeline. |
| Replay `predict.decide_case()` ngày 11/10 | Khớp 8/8 nhãn công khai; 8/8 còn ít nhất một rule unknown | Tám PDF thật và câu trả lời GPT đã lưu; **không gọi GPT mới**. Case 03 đổi nhãn sau khi sửa cổng giai đoạn. |
| Test tổng hợp | 9/9 pass | Kiểm cơ học một số biến thể về số tiền, báo giá, phạm vi, giai đoạn; không đo khả năng tổng quát của model. |

Nhãn nghiệp vụ của từng rule là `pass`, `fail`, `not_applicable`. `unknown`/`rule_error` là trạng thái kỹ thuật hoặc thiếu nguồn. Khi không có `fail` nào, pipeline hiện xuất `angenommen` ngay cả khi còn `unknown`; nhãn này phải được mô tả là **tạm thời**. Bốn hồ sơ được nhận trong replay không phải bốn chứng minh tuân thủ đầy đủ.

## Từng rule: đã tune và còn thiếu gì

| Rule | Thay đổi tổng quát và bằng chứng đã có | Vấn đề chưa giải quyết / cách xử lý |
| --- | --- | --- |
| `framework_contract_sourcing` | Liên kết mặt hàng với quote phạm vi; kiểm trích dẫn, thời điểm và hạn chế suy từ danh sách mở `u.a.`. Cổng mới nhận nghĩa vụ nói về ý định `bestellen wollen` ngay lúc xin mua; replay case 03 từ chối, không có audit fail. | Chưa có lượt GPT mới sau sửa. Cổng không chứng minh mọi ngoại lệ đã được model xét đúng. Email đề xuất **chưa phải đơn đặt hàng**; không viết rằng đã mua. Rà route IT Servicezentrum ở case 03 khi tích hợp: PDF không xác lập rằng yêu cầu được gửi qua route đó. |
| `comparison_offers` | Liên kết ngoại lệ với phạm vi hàng/phương thức, xác minh số báo giá qua PDF. Case 06 có `fail` từ GPT cuối với một quote luật và hai đoạn PDF xác minh; audit độc lập cũng bắt thiếu báo giá. | Case 02 thiếu quote đúng phạm vi cho mua trực tiếp; không suy ngoại lệ catering sang hàng điện tử. Case 03 lỗi khớp excerpt; case 08 cần đọc thư bổ sung. Không tự đổi thiếu nguồn thành `pass` hoặc `not_applicable`. |
| `amount_calculation` | Mã cộng/đối chiếu net, gross và giá gốc; audit bắt case 04: €2.400 so với €3.384. Các test biến thể tính toán qua. | Rule LLM chưa có quote nghĩa vụ đúng phạm vi để công nhận `pass/fail`; kết quả phép tính là chẩn đoán, audit tự mâu thuẫn được ghi riêng. |
| `document_consistency` | Mã đối chiếu các PDF và giá báo giá gốc; audit bắt case 07: €2.350 bị chép thành €3.243. | Digest hiện có 0 quote nghĩa vụ cho rule này. Không gọi `pass/fail` chính sách từ sự vắng mặt của quote; đánh giá độ phủ với bố cục PDF khác vẫn cần làm. |
| `award_selection` | Giá lấy từ báo giá gốc; gate không nhận quote về **công bố** tiêu chí làm nghĩa vụ luôn chọn giá thấp nhất. | Hai quote đã lấy không chứng minh nghĩa vụ chọn nhà cung cấp. Rule này chủ yếu còn chẩn đoán; không tune prompt để bịa một nghĩa vụ không có trong corpus. |

Audit PDF độc lập đã góp phần vào nhãn từ chối của 04 (`form_total`), 06 (`declared_method_missing_offers`) và 07 (`offer_vs_award_note`). Ba đường audit này được xác nhận giữ nguyên trong lần gọi `decide_case` ngày 11/10. Case 03 không có audit fail; nhãn mới đến từ đường rule/model khi dùng câu trả lời đã lưu. Báo cáo tích hợp hiện chỉ lưu nhãn, ID rule unknown và audit, chưa lưu verdict chi tiết của từng rule.

## Rà phạm vi quy tắc trên corpus mua sắm

Năm rule trên là **năm rule đã triển khai và thử trên tám hồ sơ công khai**, không phải danh mục đầy đủ mọi nghĩa vụ mua sắm. Khi đọc các trang mua sắm liên quan trong corpus, có thêm bốn **ứng viên rule** sau. Chúng chưa được code, chưa chạy GPT và **không góp phần vào kết quả 8/8**:

| Ứng viên | Nguồn trong corpus và điều kiện kích hoạt | Lưu ý giai đoạn |
| --- | --- | --- |
| Thẩm quyền yêu cầu/đặt hàng | [Ablauf einer Bestellung](https://www.uni-kassel.de/intern/interne-bereiche-der-abteilungen/finanzen/materialwirtschaft/beschaffung): người phụ trách đơn vị chi phí giao việc đặt hàng. | Hồ sơ đang xin mua không tự chứng minh rằng đơn hàng đã đặt sai thẩm quyền. Cần xác định nghĩa vụ nào đến hạn trước khi duyệt. |
| Phân loại vật tư và tài sản | Cùng [trang quy trình](https://www.uni-kassel.de/intern/interne-bereiche-der-abteilungen/finanzen/materialwirtschaft/beschaffung) nêu `Verbrauchsmaterial`, `GWG`, `Anlage`; phân loại phụ thuộc khả năng dùng độc lập và giá **từng món tính theo net**. | Trang yêu cầu nhập phân loại khi đặt hàng; nếu xét hồ sơ trước khi đặt, kiểm loại đã khai và thời điểm yêu cầu trước khi gán `fail`. |
| Thủ tục thiết bị nghiên cứu đặc biệt | [Gerätefondsverfahren](https://www.uni-kassel.de/intern/interne-bereiche-der-abteilungen/finanzen/materialwirtschaft/geraetefondsverfahren) nêu điều kiện riêng cho khoản mua thuộc quỹ/thiết bị nghiên cứu: phối hợp ITS, cơ sở vật chất, yêu cầu kỹ thuật hoặc thủ tục thiết bị lớn tùy trường hợp. | Chỉ áp dụng khi hồ sơ thực sự thuộc chương trình hoặc loại thiết bị đó; không suy rộng sang mọi đơn mua. |
| Chuẩn bị nhập khẩu ngoài EU | [Informationen zum Zollverfahren](https://www.uni-kassel.de/intern/interne-bereiche-der-abteilungen/finanzen/materialwirtschaft/beschaffung/informationen-zum-zollverfahren) nêu chi phí nhập khẩu, trao đổi trước với bên bán và thủ tục hải quan. | Kiểm việc chuẩn bị trước khi đặt; khai hải quan và thông quan là bước sau. |

Thẩm quyền và phân loại có thể xuất hiện ngay trong mẫu công khai, nên không mô tả bốn ứng viên là “không liên quan tám case”. Mục đích của chúng là mở rộng phạm vi từ nghĩa vụ trong nguồn, **không bổ sung theo đáp án mẫu**. Chưa thể khẳng định chín nhóm là đủ: trang [Beschaffungsordnung / Vergaberechtliche Vorschriften](https://www.uni-kassel.de/intern/interne-bereiche-der-abteilungen/finanzen/materialwirtschaft/beschaffung/beschaffungsordnung-vergaberechtliche-vorschriften.html) giới thiệu văn bản quy định nhưng corpus trang không chứa toàn văn quy định. Bản `documents.jsonl.gz` tiếng Anh trong snapshot đọc bị cắt ở cuối; lượt rà này dựa chủ yếu vào các trang tiếng Đức đọc được. Muốn chốt độ bao phủ, cần lấy toàn văn quy định, lập danh mục nghĩa vụ và đối chiếu từng nghĩa vụ với rule trước khi code/test ứng viên.

## Phân loại việc còn mở

| Có thể sửa và đo bằng mã | Không giải được bằng prompt, hoặc chấp nhận trong pilot |
| --- | --- |
| Chuẩn hóa excerpt PDF và tách email; đo số lần trích dẫn bị gate từ chối trên hồ sơ mới. | Corpus thiếu nghĩa vụ đúng phạm vi ở rule 2/3/4/5: cần bổ sung nguồn hợp lệ hoặc giữ `policy_gap`. |
| Retry riêng lỗi endpoint với hạn chót; kiểm tổng thời gian từ index/digest đến nhãn trong 300 giây/hồ sơ. | Danh sách hợp đồng khung có `u.a.` là danh sách mở; tìm không thấy không chứng minh không tồn tại. |
| Ghi verdict, quote và lỗi gate cho từng rule ở lần kiểm tích hợp tiếp theo; kiểm test biến thể và case chưa dùng để tune. | Phân loại điều khoản, ngoại lệ và kênh mua là vấn đề ngữ nghĩa; gate chỉ kiểm tính tồn tại và liên kết nguồn, không bảo đảm model hiểu đúng. |

Không tune theo ID, mức tiền hoặc đáp án của tám case công khai. Không biến `unknown` thành `pass`, và không thay đổi phép gộp `fail` chỉ để khớp nhãn phát triển.

## Điều kiện dùng tiếp

**Có thể bàn giao ngay để partner review:** source, test, README, bảng case, trace và JSON kết quả tích hợp được giữ trong cùng một gói; nêu rõ các giới hạn ở trên. Không cần thêm một lượt GPT tốn phí chỉ để bàn giao pilot.

**Trước khi merge/nộp như pipeline thật:** chạy một lượt mới với chính mã đã chốt, xác nhận mỗi hồ sơ có đầu ra trong 300 giây tính cả chuẩn bị; rà lý do case 03 và ngoại lệ kênh IT; bảo đảm tích hợp không làm hỏng hai chủ đề công tác/hoàn ứng và Reflect của partner. Nếu thiếu một trong các kiểm tra này, tiếp tục gắn nhãn *pilot*, không mô tả là đã hoàn tất hệ thống Task 2.

Chi tiết: [quá trình tune](PROCUREMENT_TUNING.md), [kết quả từng case](CASE_RESULTS.md), [lượt GPT cuối](FINAL_REVIEW.md), [JSON tích hợp](../evidence/integration/decide-case-offline.json).
