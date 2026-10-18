from src.models import Rule

EXPENSE_REIMBURSEMENT_RULES: list[Rule] = [
    Rule(
        id="cost_purpose",
        subject='Whether each claimed expense has a substantiated connection to the institution’s work.',
        check=(
            'Subject: Whether the submitted expense has a substantiated connection to the institution\'s work. The topic says a reimbursement is requested; it is not itself evidence that each purchase served institutional work.\n'
            'Policy: Locate an applicable provision limiting reimbursement to dienstlich begründete (work-justified) expenses or stating an equivalent institutional-purpose condition. Quote that condition. A provision about identifying an item on a receipt is a different requirement. Do not invent a special form field or documentary duty that the policy does not state.\n'
            'Compare: Review ALL submitted documents for each expense. Identify any stated institutional use, beneficiary, department, project, institutional delivery or billing address, or other concrete work connection. Check whether the documents positively point to a personal purpose. Distinguish an item description from its purpose. A personal payer or home address alone does not establish personal use; an institutional addressee or department can provide a genuine work connection without identifying the payer. Use the combination of facts, not the product type, a price threshold, or a single address.\n'
            'Verdict: fail only when (a) the quoted applicable policy makes work justification a condition of reimbursement and (b) the submitted claim, considered in full, provides no identifiable connection to institutional work for the claimed expense, or positively establishes an incompatible personal purpose. Explain which condition was not substantiated, what documents were checked, and quote the material case facts; do not assert that private use is proven merely from missing work evidence. pass when an applicable policy and concrete facts substantiate institutional purpose, without requiring an invented purpose statement. unknown when the policy packet does not establish a purpose condition or material case facts are too ambiguous to resolve the connection. not_applicable only when the submitted claim contains no expense subject to this purpose check.\n'
            'Out of scope: Whether private advance was an allowed purchasing route, urgency, SAP ordering, category-specific exclusions, library acquisition, receipt form, payment proof, amounts, duplicate claims, hospitality rules and online-event procedure. An ending date for a digital submission pilot is not an eligibility cutoff. For pass or fail, supply policy_refs and case_quotes for the material facts. EACH case_quotes.quote must copy one uninterrupted substring of ONE case document. Use separate entries for a recipient/address header, an item line, and a later delivery statement; never omit intervening lines and join the remainder into one quote. To support a conclusion that the documents contain no institutional connection, cite the available recipient, item and delivery facts, then describe in the reason which documents were checked and what link is missing. A personal addressee is not proof of private use. For unknown, identify the missing policy or fact.'
        ),
        queries={
            "de": [
                "privat verauslagte Kosten Erstattung",
                "Auslagen Beschäftigte Anschaffung selbst bezahlt Erstattung",
                "Kostenerstattung Auslagen Quittung Erstattungsformular",
                "Dienstlich begründete und privat verauslagte Kosten Bedienstete Erstattung",
                "Kostenerstattung dienstlich begründete Kosten dienstlicher Zweck",
                "Erstattungsantrag Auslagen Begründung Verwendungszweck",
            ],
            "en": [
                "reimbursement of privately advanced costs",
                "employees paid purchases themselves reimbursement receipt",
                "out-of-pocket expenses refund work-related purpose",
                "work-justified privately advanced costs reimbursement university staff",
            ],
        },
        questions={
            "de": [
                "Unter welchen Voraussetzungen können Beschäftigte selbst bezahlte Kosten erstattet bekommen?",
                "Setzt die Erstattung privat verauslagter Kosten einen dienstlichen Grund voraus?",
                "Unterscheidet die Quelle zwischen dienstlicher Begründung und bloßer Artikelbezeichnung auf der Quittung?",
            ],
            "en": [
                "Under what conditions can employees be reimbursed for costs they paid themselves?",
                "What work-related purpose must costs advanced by employees have to be reimbursed?",
                "Is a documented institutional connection a condition for reimbursing an expense?",
            ],
        },
    ),

    Rule(
        id='private_purchase_eligibility',
        subject='Whether a personally paid purchase is eligible for the private-advance reimbursement route.',
        check='Subject: Whether a personally paid purchase is eligible to use the private-advance reimbursement route instead of the ordinary institutional purchasing route. Work-related purpose alone does not settle this route.\nPolicy: Identify the provision for privately advanced costs, its conditions, and any exception to ordinary purchasing. Apply funding or product-specific limits only to their stated scope.\nCompare: Identify who actually paid, what was bought, when, and any documented urgency or permitted exception.\nOut of scope: Whether the purchase had an institutional purpose, library rules for books, receipt format, arithmetic, duplicate claims, hospitality categories, and online-event fees. An invoice addressed to the institution or a personal card alone does not prove a route violation.\nVerdict: Fail only when the applicable quoted rule makes this private purchase ineligible at the claim stage and the case positively shows the violation or omits a stated mandatory justification. Pass when the documented route meets that rule. If the packet does not establish the applicable route, return unknown.',
        queries={'de': ['Kostenerstattung privat verauslagte Kosten dienstlich begründet Ausnahme',
        'Beschaffungen SAP kleinere zeitlich dringende Anschaffungen Auslagen',
        'Privat verauslagte Kosten Beschäftigte Erstattung Finanzabteilung'],
 'en': ['university reimbursement privately advanced service expenses exceptions',
        'out-of-pocket work-related purchase employee reimbursement']},
        questions={'de': ['Wann können dienstlich begründete und privat verauslagte Kosten erstattet werden?',
        'Unter welchen Voraussetzungen sind selbst besorgte Anschaffungen statt der '
        'regulären Beschaffung erstattungsfähig?'],
 'en': ['Which privately advanced costs may an employee claim from the institution?']},
    ),
    Rule(
        id='academic_book_acquisition',
        subject='Whether claimed academic books followed an applicable acquisition route.',
        check="Subject: The acquisition route for claimed academic books and literature.\nPolicy: Identify any applicable library purchasing and inventory rule, its funding scope, and the exception for literature treated as consumable material. Do not extend a grant-specific provision to other funding.\nCompare: Identify the claimed item, funding source if documented, and evidence of the actual acquisition route. An invoice from a bookseller alone does not establish that the library was bypassed.\nOut of scope: Institutional purpose, private-payment eligibility, whether an invoice is final, the amount paid, hospitality and event fees.\nVerdict: Not applicable when no book or literature is claimed. Fail only for a positively documented breach of a mandatory route with no applicable exception. Pass when the applicable route is evidenced; unknown when the policy packet does not settle its scope.\nEvidence checkpoint: Identify the actual funding scope of the quoted library rule. The title or context of a grant-administration provision cannot by itself prove all purchases use that funding. An invoice from a bookseller, even addressed to a department, does not prove the library was bypassed: libraries also buy from booksellers. To fail, cite a distinct document span establishing the non-library acquisition route and the applicable policy scope. If a book is present but either is unresolved, do not fail. Identify the actual purchased item from an item line, never from the seller's name.",
        queries={'de': ['Drittmittel Bücher grundsätzlich über Bibliothek beschaffen inventarisieren '
        'Dauerausleihe',
        'Literatur Verbrauchsmaterial Ausnahme Bibliothek Beschaffung Drittmittel',
        'Kostenerstattung Fachbuch Universitätsbibliothek Beschaffung'],
 'en': ['university grant funded academic books library purchasing inventory exception']},
        questions={'de': ['Für welche Bücher ist eine Beschaffung über die Universitätsbibliothek '
        'vorgeschrieben?',
        'Wann gilt Literatur als Verbrauchsmaterial und welche Inventarisierung ist dann '
        'nötig?',
        'Gilt diese Vorgabe für die im Antrag belegte Finanzierungsart?'],
 'en': ['Does the applicable funding policy require this academic book to be purchased '
        'through the library?']},
    ),
    Rule(
        id='reimbursement_receipt_validity',
        subject='Whether each claimed expense has a valid final receipt or invoice identifying what was bought.',
        check="Subject: Is each claimed expense supported by a valid receipt or final invoice that identifies what was bought? Check only documentary validity and item identification.\nPolicy: Quote the applicable requirement for an original receipt or allowed digital copy and the permitted keyword when the receipt does not name an article. Before using any passage, verify that its subject is reimbursement of these privately advanced expenses. Ignore limits and form requirements belonging to another kind of payment or another procedure; do not mention their monetary thresholds in the reason.\nCompare: Read every page and all submitted documents. A printed numeric article code alone does not identify the product. For a multi-line claim, inspect EVERY claimed item; one correctly described line cannot establish all the others. A numeric code, a personal name, or a masked label alone is not a product description. Look for any handwritten or typed note identifying an otherwise unclear purchase, wherever it occurs, and link it to the receipt by concrete shared context; do not assume the note is below the printed lines. A preliminary or pro-forma document that explicitly promises a later final invoice is not that final invoice merely because it bears a paid stamp. Check whether a final document was submitted. A receipt-only input does not prove that a separate application form was never filed.\nVerdict: fail if the applicable policy requires material receipt evidence and the submitted documents lack a final receipt or item identification even after a permitted note is considered. pass only when the required document is valid and ALL material claimed items are positively identified in the documents or linked notes; cite support for every otherwise unclear line. If a material label appears redacted or pseudonymized and its underlying item cannot be established, return unknown for this receipt check and name that line: do not treat pseudonymization alone as a policy violation. fail only for a proven missing mandatory document or product identification under the applicable policy, not for uncertainty caused by masking. unknown also applies when the governing policy is unresolved; say what is missing. not_applicable only if no claimed expense needs receipt validation. Never copy another rule's verdict.\nEvidence: For fail/pass, cite the governing policy and SHORT verbatim case excerpts. Each case quote must be ONE continuous span from ONE document. If the document title/status and a later sentence saying a final invoice is forthcoming are separated, make TWO entries; never join them with newlines or an ellipsis. For a coded receipt, cite the actual identifying note as well as the relevant receipt line, each separately. A case quote must contain the words relied on in the reason.\nOut of scope: Purpose, purchasing route, excluded categories, credits, arithmetic and duplicate claims.\nDocument-type checkpoint: A final commercial invoice identifying the purchased item, amount and transaction may itself be original evidence of the expense. Do not reject an otherwise final, itemized invoice merely because it is titled Invoice instead of Quittung. Apply a stricter document-type condition only if the cited policy expressly excludes that final invoice. An expressly pro-forma document that promises a later final invoice is different.",
        queries={'de': ['Kostenerstattung Erstattungsformular Originalquittung Artikel Stichwort',
        'Digitale Abrechnung privat verauslagter Kosten Belege Originalbelege',
        'Auslagen Erstattung Quittung Rechnung Zahlungsnachweis Beleg'],
 'en': ['reimbursement original receipt item description proof of payment']},
        questions={'de': ['Welche Belege sind zur Erstattung privat verauslagter Kosten erforderlich?',
        'Was ist bei einer Quittung ohne ausgewiesenen Artikel zu ergänzen?',
        'Welche Originalbelege oder hochgeladenen Belege verlangt das geltende Verfahren?'],
 'en': ['What invoice or receipt evidence supports an out-of-pocket reimbursement?']},
    ),
    Rule(
        id='actual_expense_reconciliation',
        subject='Whether the reimbursement evidence represents distinct costs actually advanced and still borne after credits.',
        check="Subject: Whether the reimbursement evidence represents costs actually advanced by the claimant and still borne after refunds. Submitted invoices and receipts are the evidence under review, even without a separate claim-line form.\nPolicy: Quote the applicable passage limiting reimbursement to privately advanced costs. If it does not expressly address duplicate invoices or credits, say so. Treat a repeated document for one underlying cost as an inference from that reimbursement scope; never attribute an express duplicate ban to a passage that lacks it.\nCompare: Group documents by the underlying transaction, using seller, order/reference, items and quantities, amounts, payment details, corrections, deliveries and credits together. A reprint, replacement or second invoice number is not automatically a second cost; a shared order can cover distinct paid lines. Determine whether two invoices describe one payment or separate expenses. For a credit, identify the invoice it corrects and calculate the net cost actually borne using the documented amounts. Do not infer that two charges occurred merely because two invoices say paid, and do not invent a claim total.\nVerdict: fail only when corroborating evidence across the documents strongly supports that one cost is presented twice for reimbursement without a distinct second charge, delivery or correction explaining it. A separate claim-line form is not required to assess two submitted invoices. State the factual inference separately from what the policy actually says. pass if an applicable comparison of documented costs, claim amount and credits reconciles to distinct underlying expenses. not_applicable when there is no reconciliation question, such as a lone invoice or receipt without another charge, credit, correction or explicitly claimed amount to compare. unknown only if a material transaction fact or applicable policy needed for an active reconciliation genuinely remains unresolved.\nEvidence: A fail needs separate, exact, short PDF spans from each relevant invoice supporting the shared reference, item or amount, payment detail and differing document number. A pass involving a credit needs exact spans for both invoice amounts, the credit amount, its link to the corrected invoice and any submitted net calculation. Quote one uninterrupted span per entry. Before writing the reason, check every factual assertion against those spans: do not claim different orders when the references show a reprint of the same order. The final reason must distinguish the quoted policy from the case-based inference.\nOut of scope: Work purpose, purchasing route, books, receipt finality, hospitality categories and online-event procedure. A document's type or lack of final-invoice status alone cannot fail this reconciliation rule; assess its validity under the separate receipt rule.\nCitation checkpoint: For each invoice you compare, cite the exact order-reference line and one exact amount or item line as SEPARATE case_quotes entries. Cite the different invoice numbers separately when relevant. Copy each physical line verbatim from the identified PDF. Never manufacture a contiguous paragraph by removing intermediate lines, labels or columns. Before submitting JSON, verify every case_quotes.quote is literally present in its own source document; otherwise return unknown.",
        queries={'de': ['privat verauslagte Kosten Auslagen Erstattung Belege',
        'Kostenerstattung Rechnung Gutschrift Rückerstattung tatsächlich verauslagt',
        'Abrechnung privat verauslagter Kosten Rechnung Zahlungsnachweis'],
 'en': ['reimbursement actual out-of-pocket expense credit refund duplicate receipt']},
        questions={'de': ['Welche tatsächlich privat verauslagten Kosten werden erstattet und welche Belege '
        'sind vorzulegen?',
        'Wie werden Gutschriften und Rückzahlungen bei einer Erstattung berücksichtigt?'],
 'en': ['Is reimbursement limited to evidenced costs actually paid by the claimant?']},
    ),
    Rule(
        id='hospitality_and_refreshments',
        subject='Whether claimed food, beverages, gifts or hospitality satisfy the applicable representation policy.',
        check="Subject: Eligibility of claimed food, beverages, gifts or hospitality under the institution's representation policy. Judge the readable food and drink lines on a mixed invoice separately from durable equipment. This rule cannot reject a kettle or mugs as hospitality expenses.\nPolicy: Read the exact scope of each passage. A provision saying that modest refreshments offered to university guests are ordinary operating expenses describes a guest-courtesy category; it neither bans all operating expenses nor proves that every purchase of coffee or tea was for guests. A separate exclusion concerns hospitality at which no external persons participated. Cite both provisions when assessing possible internal consumption. Apply event, funding and documentation conditions only to the category they actually govern.\nCompare: First identify the readable claimed food or beverage lines. Then assess their intended use from the documents together: destination, stated purpose or occasion, participants, and any accompanying pantry supplies or equipment. A departmental pantry destination together with consumables and pantry equipment can support an inference of routine internal supply; label that inference honestly. A university address alone, a missing guest list alone, or an absence of the word guest alone does not establish staff-only hospitality. A positive mention of guests or an external event must be reconciled before finding internal use. Do not infer the type of an unidentified, masked or pseudonymized line.\nVerdict: not_applicable when no food, beverage, gift or hospitality line is claimed. fail only if concrete case evidence supports a use excluded by the applicable quoted provision, or establishes that a mandatory condition for the claimed use is materially unmet. For a routine internal pantry inference, require a readable consumable line plus multiple mutually supporting facts about its intended departmental use; explain that the use is inferred rather than written explicitly. Do not treat guest courtesy as a prohibition or treat equipment as the offending item. pass when the applicable permission and its conditions are positively supported. unknown if an alternative guest use, governing category, or material condition remains genuinely unresolved; name the unresolved fact.\nEvidence: For a fail, cite exact, separate PDF spans for each materially distinct offending food or beverage line and for the destination or occasion. You may cite equipment as corroborating context, but never as the offending food item. Cite the exact policy passage containing the staff-only exclusion and the conditional guest-courtesy passage, and state which is being applied and why. Each case quote must be one uninterrupted span from one document. The reason must separate a source-backed policy statement from an inference based on the case facts. If a required span cannot be verified, return unknown.\nOut of scope: Equipment eligibility, ordinary purchasing route, institutional purpose in general, receipt form and item-label validity, amounts, credits, duplicate claims and online-event fees.",
        queries={'de': ['Bewirtungskostenrichtlinie Universität Gäste dienstlicher Zweck Erstattung',
        'Nicht erstattungsfähige Bewirtung keine externen Personen Arbeitsessen',
        'übliche Gesten Höflichkeit Mineralwasser Kaffee Tee Gäste Landesmittel',
        'Bewirtungsbeleg Rechnung Anlass Teilnehmerliste Drittmittel'],
 'en': ['university hospitality reimbursement external guests staff refreshments '
        'exception']},
        questions={'de': ['Wann sind Bewirtungsaufwendungen erstattungsfähig und welche Ausgaben sind '
        'ausgeschlossen?',
        'Welche üblichen Gesten der Höflichkeit für Gäste sind keine Bewirtungskosten?',
        'Welche Angaben zu Anlass, Teilnehmenden, Finanzierung und Beleg sind nötig?'],
 'en': ['Which hospitality costs for external guests are reimbursable and what evidence is '
        'required?']},
    ),
    Rule(
        id='online_event_fee_route',
        subject='Which reimbursement route applies to a participation fee for an online-only event.',
        check='Subject: Which reimbursement process handles a participation fee for an online-only event.\nPolicy: Identify the applicable provision routing online conference or event fees through private-cost reimbursement or travel expenses.\nCompare: Determine whether the claim is for online-only participation and which route the documents positively show.\nOut of scope: Whether the event served an institutional purpose, whether the fee amount was paid, receipt validity and travel approval. A foreign organizer or currency does not turn a virtual event into a physical trip.\nVerdict: Not applicable to other costs. Fail only if an incompatible route is documented and the quoted rule makes that route material at this stage. Pass when the documented route fits; unknown when the policy packet does not establish the route.',
        queries={'de': ['Online Konferenzen Tagungen Teilnahmegebühren Privat Verauslagte Kosten',
        'online Konferenzen keine Dienstreisen Formular Finanzabteilung',
        'Teilnahmegebühren virtuelle Tagung Reisekostenabrechnung Fiori'],
 'en': ['online conference registration fee privately advanced costs reimbursement route']},
        questions={'de': ['Wie werden Teilnahmegebühren für Online-Konferenzen oder Online-Tagungen geltend '
        'gemacht?',
        'Ist für eine reine Online-Konferenz eine Dienstreise oder Reisekostenabrechnung '
        'einzureichen?'],
 'en': ['Which process reimburses fees for an online-only conference?']},
    ),
]
