# Procurement: nhật ký tune từng rule

Đây là file theo dõi chính trong `runs/procurement/`. Mỗi thư mục chạy giữ
`stdout.log`, trace và báo cáo gốc. Cập nhật kết luận sau khi đọc bằng chứng;
nhãn nhị phân của một rule riêng không phải độ chính xác toàn pipeline.

| Rule | Trạng thái hiện tại | Việc cần kiểm tra tiếp |
| --- | --- | --- |
| 1. `framework_contract_sourcing` | Đã thử GPT trên 8 hồ sơ, chưa chốt tổng quát | Rà căn cứ scope/ngoại lệ case 03; case 06 và 08 từng thiếu căn cứ để kết luận áp dụng. |
| 2. `comparison_offers` | Đã thử GPT, còn lỗi | Case 02 lấy ngoại lệ dưới €1.000 của catering áp sang thiết bị điện tử; case 08 diễn giải ngưỡng không có trong quote chung. Case 06 có căn cứ về 2/3 báo giá. Sửa nguồn/phạm vi bằng offline replay, chưa gọi GPT lại. |
| 3. `amount_calculation` | Kiểm tra phép tính trong PDF bằng mã | Case 04: 2.220 + 180 = 2.400 netto, đơn ghi 3.384. Case 02: email thiếu thuế suất để kiểm netto/brutto ngay trên email; báo giá đính kèm có dòng thuế. Đây là chẩn đoán, chưa gán verdict nghiệp vụ. |
| 4. `document_consistency` | Audit offline v2 trên 8 hồ sơ; GPT digest trả 0 quote | Case 04 và 07 có sai lệch tài liệu; chưa có nguồn luật áp dụng ở giai đoạn xin mua để gán verdict. |
| 5. `award_selection` | Audit offline 8 hồ sơ; GPT trên 01/07 chưa xác minh được verdict policy | Case 01 khớp tiêu chí ghi trong biên bản nhưng `pass` chưa được quote luật chứng minh; case 07 lệch giá và `rule_error` vì thiếu luật đúng phạm vi. |

## Các lượt đã chạy

| Rule/lượt | Kết quả cần giữ |
| --- | --- |
| [`framework_contract_sourcing-20261008-233538`](framework_contract_sourcing-20261008-233538/) | GPT, 8 hồ sơ; một rule, chưa kết luận cả task. |
| [`comparison_offers-20261009-000540`](comparison_offers-20261009-000540/) | GPT, 8 hồ sơ; bản trước khi rút gọn. |
| [`comparison_offers_cached-20261009-110950`](comparison_offers_cached-20261009-110950/) | GPT trên 8 hồ sơ, tái dùng 4 quote; case 02 `pass` sai căn cứ. |

## Các lượt rule 3

| Thư mục báo cáo | Chẩn đoán |
| --- | --- |
<!-- RULE3_RUNS_START -->
| [amount_calculation-20261009-112819](amount_calculation-20261009-112819/amount-audit.json) | 1 discrepancy, 1 needs review, 6 checked |
<!-- RULE3_RUNS_END -->

## Nguyên tắc cập nhật

- Sau mỗi lượt, ghi file output, ngày chạy, bằng chứng đúng/sai, lỗi còn mở,
  và quyết định tiếp theo tại đây. Giữ các trace để kiểm tra lại.
- `discrepancy`, `checked`, `needs_review` trong báo cáo rule 3 là **trạng thái
  chẩn đoán**, không phải `pass`/`fail`/`not_applicable` của pipeline.
- Không dùng 8 nhãn public để suy ra độ đúng trên hồ sơ ẩn. Các bộ hybrid
  replay dùng kết quả đã lưu, không phải lượt GPT kiểm tra lại năm rule.
- Khi chuyển rule, chỉ chạy thêm GPT nếu phép kiểm PDF và nguồn luật chưa đủ.

## Các lượt rule 4

| Báo cáo | Chẩn đoán |
| --- | --- |
<!-- RULE4_RUNS_START -->
| [document_consistency-20261009-113546](document_consistency-20261009-113546/consistency-audit.json) | 2 discrepancy, 1 needs review, 5 checked |
| [document_consistency_v2-20261009-204823](document_consistency_v2-20261009-204823/consistency-audit.json) | 2 discrepancy, 1 needs review, 5 checked |
<!-- RULE4_RUNS_END -->

## GPT: rule 3 `amount_calculation`

Một lần resolve policy và tám lượt GPT kiểm tra hồ sơ; so với chẩn đoán offline sau khi đọc trace. Nhãn ở đây thuộc một rule, không phải kết quả toàn task.

| Run | Verdict thô, chưa rà bằng chứng |
| --- | --- |
<!-- RULE3_GPT_RUNS_START -->
| [amount_calculation_gpt-20261009-185203](amount_calculation_gpt-20261009-185203/rule-results.json) | 4 policy quotes; 7 pass, 1 unknown |
<!-- RULE3_GPT_RUNS_END -->

<!-- SCOPE_AMOUNT_RUNS_START -->
## Scoped procurement trials

| Run | Status |
|---|---|
| [comparison_scope-20261009-195233](comparison_scope-20261009-195233/rule-results.json) | 0/1 decided; inspect rule errors and evidence |
| [Rule 3 amount-scope-audit-20261009-194935](amount-scope-audit-20261009-194935/amount-audit.json) | 1 arithmetic discrepancies; no policy verdict |
<!-- SCOPE_AMOUNT_RUNS_END -->

## Rule 2 policy coverage, case 02

Offline corpus scan: the under 1,000 EUR direct award passage is limited to
catering, while the general regulation's supplied body has only an introduction.
The retrieved packet therefore does not establish the proposed electronics
exception. See `policy-gap-case02/coverage.json`. Repeating GPT with the same
four quotes cannot fill this source gap; rule_error preserves the evidence.

## Rule 4 v2: kết quả kiểm chéo

Đã chạy mã offline trên 8 hồ sơ. Case 04 có tổng trên đơn khác báo giá được
chọn; số hiệu báo giá bị xuống dòng trong biên bản đã được ghép đúng, nên không
còn coverage gap giả. Case 07 có giá báo giá khác giá chép trong biên bản.
Case 03 không có báo giá hoặc giỏ hàng liên kết để đối chiếu. Đây là bằng
chứng nhất quán tài liệu, chưa phải verdict nghiệp vụ. Xem lượt v2 mới nhất ở
bảng báo cáo rule 4 phía trên và các trích dẫn trong consistency-audit.json.

## Rule 5: award selection (offline)

| Lượt | Contradiction | Consistent | Review | No note |
| --- | ---: | ---: | ---: | ---: |
| [award_selection-20261009-205749](award_selection-20261009-205749/selection-audit.json) | 1 | 3 | 0 | 4 |
<!-- RULE5_RUNS_END -->

## GPT rule 4: document consistency

Model đánh giá quy định áp dụng cho chênh lệch đã phát hiện bằng mã. Đây là thử nghiệm một rule, chưa ghi đè nhãn hồ sơ.

| Run | Kết quả sơ bộ |
| --- | --- |
<!-- RULE4_GPT_RUNS_START -->
| [document_consistency_gpt-20261009-210540](document_consistency_gpt-20261009-210540/rule-results.json) | 0 quotes; 03: rule_error, 04: rule_error, 07: rule_error |
<!-- RULE4_GPT_RUNS_END -->

## Rule 2–4: kiểm toán nguồn và dữ kiện

Quét toàn bộ corpus được cấp, giữ ứng viên để rà văn bản đầy đủ. Rule 3/4 là chẩn đoán có nguồn PDF; không tự tạo verdict. Rule 2 chỉ ghi policy gap khi gate đã xác nhận trong trace. Xem báo cáo từng lượt; kết quả cũ không bị ghi đè.

<!-- RULE234_EVIDENCE_RUNS -->
- [rules234-evidence-20261010-002851](rules234-evidence-20261010-002851/rule2-4-readiness.json): 8 cases
- [rules234-onepass-20261010-010321-2476](rules234-onepass-20261010-010321-2476/rule2-evidence-audit.json): beschaffungsantrag-03=rule_error, beschaffungsantrag-06=needs_policy_scope_review

## GPT rule 5: award selection

Model thử đánh giá điều kiện chọn báo giá từ các quote đã truy xuất. Hai quote đều đến từ một phán quyết năm 2013 về công bố tiêu chí; chúng chưa xác lập yêu cầu phải chọn giá thấp nhất cho hai hồ sơ này. Đây là thử nghiệm một rule, chưa ghi đè nhãn hồ sơ.

| Run | Kết quả thô, chưa xác nhận policy |
| --- | --- |
<!-- RULE5_GPT_RUNS_START -->
| [award_selection_gpt-20261010-080738](award_selection_gpt-20261010-080738/rule-results.json) | 2 quotes; 01: pass, 07: rule_error |
<!-- RULE5_GPT_RUNS_END -->

### Kết luận sau khi đọc trace rule 5 (10/10/2026)

- **01:** audit PDF cho thấy nhà cung cấp được chọn có giá €2.667 netto, thấp nhất trong ba báo giá tương đương theo tiêu chí ghi trong biên bản. GPT trả `pass`, nhưng quote luật chỉ nói tiêu chí chấm phải được công bố cho người dự thầu từ trước; các quote hồ sơ chưa chứng minh điều đó. Giữ `consistent_with_stated_criterion` như chẩn đoán, chưa công nhận `pass` về policy.
- **07:** báo giá gốc M-5531 là €2.350 netto nhưng biên bản chép €3.243; đề xuất chọn báo giá €2.600, chênh €250 so với giá thấp nhất. GPT trả `unknown`, runner ghi `rule_error`, vì quote hiện tại không thiết lập nghĩa vụ chọn giá thấp nhất. Giữ sai lệch PDF trong audit; chưa tự gán `fail`.
- **Nguồn luật:** digest mất 299,53 giây, chọn hai đoạn của cùng tài liệu `hessian-law-de/LARE190016873`. Ứng viên từ Đại học Kassel trong top truy xuất nói về giao thầu từ kinh phí dự án, chưa giải quyết việc chọn báo giá của hai hồ sơ. Cần tìm và xác minh nguồn đúng phạm vi trước khi chạy lại GPT.
- **Cổng hiện tại:** runner `verified_result` chỉ kiểm có quote policy và case, chưa kiểm chúng có chứng minh lập luận. Do đó `pass` của 01 lọt qua dù nghĩa vụ được quote khác kết luận. Không tích hợp runner này vào bản nộp.
- **Thời gian:** chuẩn bị index 20,45 giây; digest 299,53 giây; check 01 là 29,87 giây và 07 là 40,23 giây (chưa kể chuẩn bị corpus). Chạy lạnh khoảng 375 giây, chưa đáp ứng mốc 300 giây nếu tính từ lúc bắt đầu. Cache policy chung có thể giảm chi phí cho các hồ sơ sau, nhưng quote hiện tại chưa đủ tốt để dùng làm căn cứ phán quyết.

## Trạng thái để bàn giao

| Nhóm | Đã kiểm được | Còn nghẽn | Quyết định hiện tại |
| --- | --- | --- | --- |
| Rule 1: framework | Đã chạy GPT 8 hồ sơ, cổng scope/citation được thử | Phạm vi hàng hóa, ngoại lệ và giai đoạn đặt mua cần rà | Giữ pilot, không lấy 8 nhãn làm chứng nhận tổng quát. |
| Rule 2: offers | Preflight toàn bộ 8; GPT riêng 03/06; audit trace | 03 sai dữ kiện số liên kết và thiếu quote gắn nghĩa vụ với email xin mua; 06 ngoại lệ/phạm vi chưa rõ | 03 `rule_error`, 06 `needs_policy_scope_review` trong audit, không đổi verdict của model một cách âm thầm. |
| Rule 3: amount | Audit phép tính PDF 8 hồ sơ; 04 có chênh lệch | Chưa có nghĩa vụ policy thích hợp để chuyển chẩn đoán thành verdict | Giữ chẩn đoán, không ép `pass/fail`. |
| Rule 4: consistency | Audit đối chiếu PDF 8 hồ sơ; 04/07 lệch, 03 thiếu tài liệu đối chiếu | Digest GPT trả 0 quote | Giữ chẩn đoán, không ép `pass/fail`. |
| Rule 5: award | Audit 8 hồ sơ; GPT 01/07 | Truy xuất cùng một án lệ và cổng chỉ kiểm quote tồn tại | Giữ chẩn đoán, chưa công nhận `pass` 01 hoặc `fail` 07. |

**Bước tiếp:** một lượt rà nguồn luật và phạm vi cho rule 2, 5; thêm cổng liên kết *nghĩa vụ trong quote → dữ kiện PDF → verdict* dùng chung. Dùng cache khi nguồn đã đạt, đo cả thời gian chuẩn bị trong ngân sách chạy. Nếu nguồn vẫn thiếu, ghi `rule_error` kỹ thuật và giữ audit; không bịa `not_applicable` hay `pass`. Chưa có bằng chứng cải thiện trên hồ sơ ẩn hoặc trên cả ba task, nên chưa chuyển pilot vào bản submit.

## Audit tiering trên 8 PDF (10/10/2026)

| Lượt | Mục đích | Kết quả |
| --- | --- | --- |
| [tiering-eight-20261010-093335-1104](tiering-eight-20261010-093335-1104/comparison.json) | So finding PDF trước/sau patch trong pilot, không gọi GPT | 8/8 hồ sơ audit chạy; 0 finding tự thành `fail` |

- **Case 04:** ngoài `form_total` đã có, bản sau tìm thêm `request_vs_chosen_offer`: tổng hai dòng và báo giá gốc là €2.400 netto, đơn ghi €3.384. Đây là hai góc nhìn của cùng sai lệch €984, **không** tính là hai lỗi độc lập.
- **Case 07:** finding `offer_amount_changed_in_award_note` của bản cũ được thay bằng `offer_vs_award_note` trong mã kiểm chéo chặt hơn. Cả hai cùng phản ánh báo giá gốc M-5531 €2.350 netto nhưng biên bản chép €3.243. Finding `selected_above_cheapest_equivalent_offer` vẫn tồn tại ở dạng chẩn đoán: đề xuất chọn €2.600, hơn giá gốc thấp nhất €250.
- Các case 01, 02, 03, 05, 06, 08 không có finding từ audit này. **Không tìm thấy finding không chứng minh hồ sơ đạt mọi quy tắc.**
- `automatic_audit_failures=0` vì `SELF_CONTRADICTION_KINDS` đang rỗng và cổng quote từ vựng chỉ chẩn đoán, chưa xác minh scope, giai đoạn và ngoại lệ. Điều này ngăn đường `audit → fail` vô điều kiện của hybrid v8. Đây **không phải** kết quả kiểm tra nhãn cuối hay chất lượng GPT.
- Giữ `before.json`, `after.json`, `comparison.json` để đối chiếu. Lượt v3 trước đó in “Đã áp” nhưng `git apply` trong thư mục con đã bỏ qua patch; v4 áp từ gốc repo và xác nhận `classify` cả trên host và Docker. Backup mã thực trước khi áp là `../procurement-before-tiering-20261010-094127.tar.gz` tính từ `uniagent/`.

## Giới hạn tích hợp còn mở

- `unknown` hoặc `rule_error` của rule GPT vẫn không làm `failed` thành true trong `predict.py`; nếu không có rule khác `fail`, nhãn cuối có thể là `angenommen` theo fallback. Trace cần ghi rõ các rule chưa kiểm xong. Bản audit này chưa chạy `predict.decide_case` nên chưa kiểm hồi quy nhãn cuối.
- Rule 2 và 5 còn thiếu quote nghĩa vụ đúng phạm vi; không nâng chẩn đoán PDF thành `pass/fail` bằng phép đếm từ. Rule 3 và 4 giữ trạng thái audit, cần xét điều khoản áp dụng và giai đoạn hồ sơ trước khi bật verdict.
- Chưa chứng minh toàn pipeline chạy dưới 300 giây/hồ sơ: riêng digest rule 5 từng mất 299,53 giây. Không chuyển patch này vào partner main/submit trước khi có kiểm tra trên pipeline thật.

<!-- BEGIN procurement matrix tuning 20261010 -->
## Rule-by-rule tuning status (2026-10-10)

This section records the measured result and the next change. **The next changes
listed below are planned, not installed by this run.** The 8 public cases were
used during development, so the 8/8 label match is a development-set result.

| Rule | Result in this run | What has been tuned or verified | Remaining issue and next change |
|---|---|---|---|
| `framework_contract_sourcing` | 17 policy quotes; 1 `fail` (03), 1 `pass` (05), 1 `not_applicable` (04), 5 `unknown` (01/02/06/07/08). | Product class is linked to contract scope and ordering duty; the source gate blocks unsupported quote spans and unexplained verdict changes. The `fail` on 03 matches BTC's *proposed* external webshop for framework monitors; this is not proof of an executed order. | Fix PDF quote matching and email segmentation, then replay the five source failures. An open `u.a.` list cannot prove that no framework contract exists for 04 or 08; record limited search basis rather than a global absence claim. Do not weaken the source gate merely to reduce `unknown`. |
| `comparison_offers` | 4 policy quotes; 4 `pass` (01/04/05/07), 1 `fail` (06), 3 `unknown` (02/03/08). | The policy's general three-offer duty and framework exception are checked against the stated comparison method, the explicit framework checkbox and attached offers. Both model and PDF audit identify the two-offer shortfall in 06. | For 02, verify whether a generally applicable direct-award provision is present in the corpus; the current packet does not settle the under-€1,000 claim. For 03/08, repair PDF/email excerpts; 08 must read the later reply that supplies the other two offers. Never generalize a catering-specific exception to unrelated goods. |
| `amount_calculation` | 4 policy quotes; 5 `pass` (01/02/03/05/07), 1 `not_applicable` (06), 2 `unknown` (04/08). PDF audit rejects 04. | Deterministic PDF arithmetic finds 2,400 € in form positions versus 3,384 € declared in 04. | Many model `pass` answers describe correct sums without a governing policy quote. Its 06 `not_applicable` is inconsistent because the case contains calculations; its 07 claim that amounts across documents match misses the separate award-note discrepancy. Keep numeric computations and coverage gaps in code; reserve business verdicts for a verified obligation. Check the two partial invoices in 08. |
| `document_consistency` | 0 governing quotes; 8 `unknown`; no case GPT calls for this rule. PDF audit rejects 07. | Deterministic comparison matches offer ID M-5531: original 2,350 € versus award note 3,243 €. | Search the corpus once for a relevant request-stage documentation obligation. If none exists, keep the document contradiction audit and an explicit `policy_gap`; do not invent a policy quote or coerce eight `pass` verdicts. Mark unreadable/partial tables as coverage gaps. |
| `award_selection` | 2 quotes about disclosure of evaluation criteria; 3 `unknown` (01/04/07), 5 `not_applicable` (02/03/05/06/08). | The model generally avoids asserting a universal lowest-price rule from those two quotes. | The quotes do not establish an applicable lowest-price duty. Search for the actual award criterion, if present. Case 06 has an award note and case 08 has an email proposing the selected supplier: `not_applicable` merely for lack of a formal note is too narrow. The 07 miscopied price is caught by the PDF audit, not by this rule's model reasoning. |

### One-batch next change and checks

1. Fix verifiable quote extraction; add email-message boundaries and preserve the actual matched PDF span. A citation retry cannot change the verdict without newly verified source evidence.
2. Search the corpus for the missing rule 2/3/4/5 obligations and log source, scope and rejected candidates. When absent, use technical `policy_gap`, never a business `not_applicable`.
3. Keep arithmetic, offer counting and offer-to-award comparison in deterministic PDF audit; report `coverage_gap` when extraction is incomplete. Preserve the explicit method, policy duty and exception checks before an offer-count `fail`.
4. Replay all eight cases offline after the code change. Use paired mutations: correct the totals in 04, add a third offer in 06, correct the copied award price in 07, and replace the external sourcing proposal in 03. The corresponding `fail` must disappear; analogous violations with different numbers/items must be detected.
5. Spend new GPT calls only on rules whose source packet or prompt has changed, with a fixed request cap. Report per-rule source errors, policy gaps, provisional labels and wall time. Do not tune the fallback to the public set's 4/4 label balance.

This is an isolated matrix runner; the partner's `predict.py` is not yet a five-rule
submission pipeline. Promote a validated change only after checking that its
registered rules, audit, time limit and output format work in that path.

<!-- END procurement matrix tuning 20261010 -->

<!-- PROCUREMENT_ONEPASS_OFFLINE_START -->
## Five-rule source gate: offline replay

This run replayed **saved** GPT answers against the revised gate and the eight submitted PDFs. It made no GPT, retrieval or digest calls. Its labels cannot estimate fresh-model or hidden-test accuracy.

- Output: `onepass-offline-20261010-185918/replay-report.json`.
- Labels: 5 angenommen; 3 abgelehnt.
- Cases with technical gaps: 8/8.

| Rule | pass | fail | not_applicable | technical unknown |
| --- | ---: | ---: | ---: | ---: |
| `amount_calculation` | 0 | 0 | 0 | 8 |
| `award_selection` | 0 | 0 | 4 | 4 |
| `comparison_offers` | 4 | 1 | 0 | 3 |
| `document_consistency` | 0 | 0 | 0 | 8 |
| `framework_contract_sourcing` | 1 | 0 | 1 | 6 |

Unknown remains a technical state, not a fourth business verdict. Document contradictions and qualified offer-count findings are separately visible under `audit_fails` and `audit_trace`.
<!-- PROCUREMENT_ONEPASS_OFFLINE_END -->

<!-- PROCUREMENT_FINAL_VALIDATION_START -->
## Final bounded GPT diagnostic (onepass source gate)

**Some model checks incomplete.** Live model calls: 8/8; elapsed 183.89 s.

- Raw report: [final-onepass-gpt-20261010-191147/final-report.json](final-onepass-gpt-20261010-191147/final-report.json).
- Trace: [final-onepass-gpt-20261010-191147/run-trace.jsonl.log.gz](final-onepass-gpt-20261010-191147/run-trace.jsonl.log.gz).
- Six selected rule/case checks; this is **not** a fresh 8 × 5 run, and it does not establish an 8/8 accuracy result.
- The previous offline replay of saved GPT answers matched 7/8 public labels and had technical gaps in all eight cases. Its case 03 moved to provisional acceptance when a request email was no longer treated as an executed order.
- Rule 3 still needs an applicable quoted obligation before a model pass/fail; rule 4 had zero retrieved governing quotes; rule 5's two quotes concern disclosure of award criteria, not a lowest-price duty. Their PDF arithmetic and cross-document checks remain visible separately.
- A technical `unknown` is not a business verdict. A case-level `angenommen` with no verified fail remains provisional.
- This diagnostic reused saved policy packets; it did not retest retrieval, cold startup, the whole submission pipeline, or hidden cases.

| Case | Rule | Result | Verified policy | Verified PDF | Technical reason |
| --- | --- | --- | ---: | ---: | --- |
| 03 | framework_contract_sourcing | unknown | 0 | 0 | rule_error: ordering-duty-not-shown-due-at-request-stage |
| 03 | comparison_offers | unknown | 0 | 0 | rule_error: item-text-not-in-case:E2 |
| 05 | framework_contract_sourcing | unknown | 0 | 0 | LLM error: modal-http: internal error: status Failure: ServerDisconnectedError('Server disconnected') |
| 06 | comparison_offers | fail | 1 | 2 | The procurement request for an analysizwaage and an ultraschallbad requires at least three independent offers; only two offers are supplied, with no framework partner exception stated. |
| 08 | framework_contract_sourcing | unknown | 0 | 0 | LLM error: modal-http: internal error: status Failure: ServerDisconnectedError('Server disconnected') |
| 08 | comparison_offers | unknown | 0 | 0 | LLM error: final_probe_request_budget_exhausted |

### Decision before integration

Keep the five-rule pilot isolated. Review every verified quote and the case 03 stage/exception before merging; do not change a gate to match the public label. Do not report the selected checks as a new five-rule accuracy score.
<!-- PROCUREMENT_FINAL_VALIDATION_END -->

<!-- PROCUREMENT_FINAL_REVIEW_START -->
## Đánh giá sau lượt GPT có giới hạn (10/10/2026)

Lượt `final-onepass-gpt-20261010-191147` dùng **8/8 request trong 183,89 giây** để kiểm tra sáu cặp hồ sơ–rule đã chọn. Đây là lượt GPT thật với quote policy lưu từ run trước, **không phải** chạy mới 8 hồ sơ × 5 rule, cũng không đo thời gian retrieval hoặc khởi động lạnh. Kết quả gồm **1 `fail` có trích dẫn đã xác minh và 5 `unknown` kỹ thuật**. Không suy ra độ chính xác trên tám hồ sơ từ sáu lượt này.

| Hồ sơ | Rule | Kết quả | Bằng chứng và vấn đề |
| --- | --- | --- | --- |
| 03 | `framework_contract_sourcing` | `unknown` | Cổng chặn `fail`: quote quy định cách đặt hàng, còn PDF là email xin mua; chưa chứng minh đơn hàng đã đặt hoặc nghĩa vụ đó đến hạn ở bước xin mua. Retry vẫn mắc lỗi giai đoạn. Nhãn hồ sơ trong offline replay vì thế là chấp nhận **tạm thời**, lệch nhãn công khai. |
| 03 | `comparison_offers` | `unknown` | Sau retry, đoạn mặt hàng khai trong liên kết scope không khớp nguyên văn PDF (`item-text-not-in-case:E2`). Chưa có verdict đã xác minh. |
| 05 | `framework_contract_sourcing` | `unknown` | Lượt đầu có câu trả lời nhưng trích dẫn scope/mặt hàng không qua cổng; endpoint ngắt kết nối ở lượt sửa trích dẫn. Không tính là `pass` hoặc `fail`. |
| 06 | `comparison_offers` | `fail` | Có quote quy định thông thường ba báo giá và ngoại lệ hợp đồng khung; đơn khai hai báo giá, biên bản liệt kê hai nhà cung cấp. Cổng lưu 1 quote policy và 2 đoạn PDF. Đây là **kết quả rule được xác minh trong lượt này**, không chứng minh toàn pipeline hoàn tất. |
| 08 | `framework_contract_sourcing` | `unknown` | Endpoint ngắt kết nối trước khi có câu trả lời hợp lệ. |
| 08 | `comparison_offers` | `unknown` | Hết giới hạn 8 request trước khi gọi; không có đánh giá GPT mới cho cặp này. |

**Phân biệt lỗi:** case 03 là vấn đề căn cứ/giai đoạn và định dạng quote; 05/08 framework là lỗi endpoint; 08 offers chỉ là giới hạn thử nghiệm. Không lấy `unknown` làm verdict nghiệp vụ, không hạ cổng để khớp nhãn BTC. Lượt offline trước đó khớp **7/8 nhãn công khai và cả 8 hồ sơ đều degraded**; đó là replay câu trả lời GPT cũ trên mã mới, không phải kết quả của lượt GPT này. Rule 3 còn thiếu quote nghĩa vụ phù hợp cho `pass/fail`, rule 4 có 0 quote, và quote rule 5 chỉ nói về công bố tiêu chí, chưa thiết lập nghĩa vụ chọn giá thấp nhất. Các chẩn đoán phép tính và đối chiếu PDF vẫn hữu ích nhưng không tự thay thế policy.

**Quyết định bàn giao:** giữ code procurement trong nhánh/bản sao độc lập; chưa merge vào partner main hoặc push. Cần xác minh quy định tại giai đoạn xin mua cho case 03, sửa khớp excerpt mà không sửa verdict, tìm quote còn thiếu cho rule 2–5, rồi kiểm tra đường chạy lạnh dưới 300 giây/hồ sơ trước khi tích hợp. Đừng chạy thêm GPT với cùng packet để cứu điểm public. Xem `final-report.json`, `run-trace.jsonl.log.gz` và `stdout.log` trong thư mục run để phân biệt từng nguyên nhân.
<!-- PROCUREMENT_FINAL_REVIEW_END -->
