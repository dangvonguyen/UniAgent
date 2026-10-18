from src.models import Rule


TASK2_PROCUREMENT_RULES: list[Rule] = [
    Rule(
            id="comparison_offers",
            check=(
                "Subject: Review the number of independent comparison offers submitted for the "
                "proposed purchase. Identify the goods or services, stated procurement method, "
                "value and tax basis, and actual offer documents. Read dated emails in order; a "
                "later response can supply an offer.\n"
                "Policy: Cite the applicable offer requirement, its product and method scope, "
                "value basis and exceptions, including direct award or framework call-off. A "
                "general default does not settle an exception. A merely possible procedure is "
                "not mandatory for every purchase; a pointer to another rule does not provide "
                "that missing rule.\n"
                "Compare: Count independent offers evidenced by submitted offer documents "
                "rather than a stated count. Match each threshold and exception to the case's "
                "goods or services, method and value basis. If a direct-award claim cannot be "
                "assessed with the retrieved policy, report the missing provision instead of "
                "presuming the exception valid or invalid.\n"
                "Out of scope: Leave framework supplier and channel, arithmetic and award "
                "ranking to their own rules. Do not treat missing policy as proof of "
                "non-applicability.\n"
                "Verdict: fail only when an applicable quoted duty requires more offers than "
                "the complete packet shows and no exception remains unresolved; pass only when "
                "the requirement or a quoted exception is verified. Use not_applicable only for "
                "positively established exclusion. Otherwise unknown, prefixed missing_policy, "
                "scope_unresolved, case_fact_missing or conflicting_sources.\n"
            ),
            queries={
                "de": [
                    "Beschaffung Vergleichsangebote Anzahl einholen Ausnahmen Rahmenvertrag",
                    "Vergabe Preisvergleich schriftliche Angebote Direktauftrag Wertgrenze",
                    "Beschaffungsordnung Vergabeverfahren Direktauftrag Angebote Ausnahmen",
                    "Rahmenvertrag Vergleichsangebote entfallen Beschaffung",
                    "Beschaffung Direktauftrag Vergleichsangebote Wertgrenze Einkauf",
                    "Beschaffungsordnung Direktvergabe Direktkauf Beschaffungswert ohne Vergleichsangebote",
                    "drei Angebote grundsätzlich Ausnahmen Direktauftrag Vergabeverfahren",
                ],
                "en": [
                    "university procurement comparison offers direct award exception",
                    "procurement number of quotations framework agreement exemption",
                ],
            },
            questions={
                "de": [
                    "Wann sind bei Beschaffungen Vergleichsangebote einzuholen, und welche Ausnahmen gelten?",
                    "Wie bestimmen Auftragswert und Vergabeart die erforderlichen Angebote und Nachweise?",
                    "Wann entfallen Vergleichsangebote bei Direktauftrag oder Rahmenvertrag?",
                    "Enthält die Fundstelle selbst eine Wertgrenze samt Geltungsbereich, oder verweist sie nur auf eine andere Ordnung?",
                ],
                "en": [
                    "When must a procurement request include competing offers, and what exceptions apply?",
                    "How do order value, direct award and framework contracts affect offer requirements?",
                ],
            },
        ),
    Rule(
            id="amount_calculation",
            check=(
                "Subject: Review request-stage monetary amounts and any supplied verified "
                "arithmetic audit. Identify operands, document excerpts and the stated net or "
                "gross basis. If no audit exists, report stated figures without inventing VAT, "
                "discounts or missing rows.\n"
                "Policy: Cite a retrieved obligation governing the request-stage amount or "
                "calculation, including its scope, tax basis and exceptions. Do not infer a "
                "tolerance or threshold from another product category.\n"
                "Compare: Compare the verified figures with the applicable obligation. Preserve "
                "document boundaries and any audit anomaly; do not replace a supplied verified "
                "calculation with model arithmetic. Missing or conflicting components may mean "
                "extraction is incomplete.\n"
                "Out of scope: Leave cross-document offer identity to document_consistency, "
                "selection among offers to award_selection and offer count to "
                "comparison_offers. Arithmetic discrepancy alone remains an audit finding "
                "without a policy verdict.\n"
                "Verdict: fail only for a verified material breach of the quoted duty; pass "
                "only for verified compliance; not_applicable only when no monetary subject "
                "occurs or cited scope excludes the case. Otherwise unknown, prefixed "
                "missing_policy, scope_unresolved, case_fact_missing or conflicting_sources.\n"
            ),
            queries={
                "de": [
                    "Beschaffungsantrag Gesamtbetrag Nettobetrag Bruttobetrag Umsatzsteuer Berechnung",
                    "Beschaffung Auftragssumme voraussichtlicher Auftragswert Preisangaben",
                    "Vergabe Kostenberechnung Angebotssumme rechnerische Prüfung",
                    "Beschaffungsrichtlinie Mittelbedarf Kostenschätzung Betrag Bestellung",
                ],
                "en": [
                    "university procurement request amount calculation net gross tax approval",
                    "procurement estimated contract value offer arithmetic pricing requirements",
                ],
            },
            questions={
                "de": [
                    "Welche Vorgaben gelten für die Angabe und rechnerische Prüfung des Auftragswerts im Beschaffungsantrag?",
                    "Wann muss die Kostenschätzung vor der Bestellung netto oder brutto nachvollziehbar sein?",
                ],
                "en": [
                    "What policy requires a correct amount or cost estimate at procurement request stage?",
                    "How should net, gross and tax amounts be documented before an order?",
                ],
            },
        ),
    Rule(
        id="document_consistency",
        check=(
            "Subject: Review contradictions between documents in a pre-order request, "
                "including copied offer prices and matching the request to its supporting offer "
                "or basket. This rule owns cross-document transcription and identity findings.\n"
                "Policy: Cite a retrieved duty requiring consistent or accurate request "
                "information or supporting documents at this stage, including its scope and "
                "exceptions. A factual discrepancy alone does not establish a policy breach.\n"
                "Compare: Use a supplied verified document audit where available. Match the "
                "same offer, quantity and net or gross basis; an invoice may cover only part of "
                "an order. Compare an award note's copied price with the original offer. "
                "Without an audit, use only comparisons supported by the PDFs.\n"
                "Out of scope: Leave offer count, framework sourcing and whether a selected "
                "offer is preferable to their respective rules.\n"
                "Verdict: fail only for a verified material discrepancy breaching an applicable "
                "quoted duty; pass only when the duty and documents establish compliance; "
                "not_applicable when no comparable document subject occurs or cited scope "
                "excludes it. Otherwise unknown, prefixed missing_policy, scope_unresolved, "
                "case_fact_missing or conflicting_sources. Cite case and policy excerpts for "
                "pass or fail.\n"
        ),
        queries={
            "de": [
                "Beschaffungsantrag Angaben Angebot Kostenschätzung Richtigkeit Unterlagen",
                "Beschaffung Antrag beigefügte Angebote Preisangaben Prüfung vor Bestellung",
                "Vergabevermerk Angebotssumme Begründung Dokumentation Beschaffung",
                "Beschaffungsrichtlinie Vollständigkeit Nachweise Antrag Auftragssumme",
            ],
            "en": [
                "university procurement request supporting offers price consistency before order",
                "procurement documentation requirement quoted price application approval",
            ],
        },
        questions={
            "de": [
                "Welche verbindlichen Angaben oder Belege muss ein Beschaffungsantrag vor der Bestellung enthalten?",
                "Muss der beantragte Betrag mit dem eindeutig zugeordneten Angebot oder Warenkorb übereinstimmen?",
            ],
            "en": [
                "Does policy require an accurate request total or linked offer at the pre-order stage?",
            ],
        },
    ),
    Rule(
        id="award_selection",
        check=(
            "Subject: Review a proposed choice among comparable independent offers before "
                "ordering. Identify the proposed choice, original offer prices and any "
                "criterion stated in the case. A missing award note alone is not a breach.\n"
                "Policy: Cite a stage-applicable selection obligation, its scope and "
                "exceptions. The applicant's criterion is not automatically a policy duty; an "
                "obligation to announce criteria does not mean the lowest price must win. "
                "Consider quality and permitted justifications where the policy requires them.\n"
                "Compare: Use verified document audit facts for offer identity and original "
                "prices. Compare the proposal and supported justification against the quoted "
                "selection duty, not an assumed lowest-price rule.\n"
                "Out of scope: Leave copied-price contradictions to document_consistency, and "
                "framework sourcing, offer count and independent arithmetic to their respective "
                "rules.\n"
                "Verdict: fail only for a material breach of the quoted selection duty with no "
                "supported justification or exception; pass only for verified compliance; "
                "not_applicable when no choice among offers is proposed or cited scope excludes "
                "it. Otherwise unknown, prefixed missing_policy, scope_unresolved, "
                "case_fact_missing or conflicting_sources. Cite short case and policy excerpts "
                "for pass or fail.\n"
        ),
        queries={
            "de": [
                "Beschaffungsordnung Angebot auswählen Preisvergleich Begründung Beschaffungsantrag",
                "Beschaffung Hochschule wirtschaftlichstes Angebot auswählen Preis Qualität",
                "Beschaffungsrichtlinie günstigstes geeignetes Angebot Auswahl Begründung",
                "interne Beschaffung Vergleichsangebote Auswahl Entscheidung vor Bestellung",
            ],
            "en": [
                "university internal purchasing choose offer price comparison justification",
                "procurement request select suitable economic offer before order",
            ],
        },
        questions={
            "de": [
                "Welches verbindliche Kriterium gilt für die Auswahl unter vergleichbaren Angeboten vor dem Zuschlag?",
                "Wann darf ein teureres Angebot gewählt werden und welche Begründung ist erforderlich?",
            ],
            "en": ["What policy governs selection among offers at award stage?"],
        },
    ),
    Rule(
            id="request_and_order_authority",
            check=(
                "Subject: Review who may request, approve and place an order at the current "
                "stage. Identify the requester, proposed approver, signatures and documented "
                "delegation. Distinguish approval of a request from the later act of ordering.\n"
                "Policy: Cite a binding provision specifying the competent person, timing and "
                "any delegation or exception. Apply an email chain or device-specific workflow "
                "only to the product and process it expressly covers. An organizational task "
                "list alone does not impose a mandatory request-stage approval.\n"
                "Compare: Compare the documented actors and signatures against only duties "
                "already due at the request stage. An email sent by staff can convey an order "
                "commissioned by the authorized person: read explicit commissioning evidence "
                "and the recipient chain before judging it. The sender name, a CC recipient, "
                "or missing earlier emails in a partial packet alone proves no unauthorized "
                "order or skipped step. A blank field reserved for a later stage does not by "
                "itself show a breach.\n"
                "An emailed request stating that the authorized person commissioned the "
                "purchase is affirmative case evidence unless another document contradicts "
                "it. An optional written record does not make a separate signature mandatory.\n"
                "Out of scope: Leave supplier and contract scope, offer count and price "
                "calculations to other rules; do not turn a later ordering duty into an earlier "
                "approval duty.\n"
                "Verdict: fail for a verified breach of a cited duty already due; pass for "
                "verified compliance; not_applicable only if the subject does not occur or "
                "cited scope excludes the case. Otherwise unknown, prefixed missing_policy, "
                "scope_unresolved, case_fact_missing or conflicting_sources.\n"
            ),
            queries={
                "de": [
                    "Beschaffungsantrag Antragsberechtigung Zeichnungsberechtigung Genehmigung Bestellung",
                    "Beschaffung Bevollmächtigung Budgetverantwortliche Freigabe Zuständigkeit",
                    "Bestellberechtigung Hochschule Beschaffungsstelle Vollmacht",
                    "Beschaffung darf bestellen ist berechtigt genehmigen beauftragen",
                ],
                "en": [
                    "university purchase request approval ordering authority delegation",
                    "procurement budget holder signatory authorized to place order",
                ],
            },
            questions={
                "de": [
                    "Wer darf einen Beschaffungsantrag stellen, freigeben und eine Bestellung auslösen?",
                    "Zu welchem Zeitpunkt ist welche Zustimmung oder Unterschrift erforderlich?",
                ],
                "en": [
                    "Which request-stage approvals and delegated authorities are mandatory?",
                ],
            },
        ),
    Rule(
            id="asset_classification",
            check=(
                "Subject: Review classification of each requested asset or consumable at the "
                "pre-order stage. Identify the item's nature, quantity, value and stated net or "
                "gross basis from the case or verified audit.\n"
                "Policy: Cite a binding classification provision, threshold, tax basis and "
                "stage of application. Where sources conflict, report supplied title, issuer "
                "and date for each; do not settle authority or recency from memory. Never "
                "assume a VAT rate or threshold.\n"
                "Compare: Compare the documented classification and amount with a duty shown to "
                "apply at the request stage. Distinguish an email asking the procurement office "
                "to place an order from the later order booking where a category must be entered. "
                "An invoice or order number alone does not show which category the office entered. "
                "A blank category in an email is not evidence that the office omitted it during "
                "booking. If metadata needed to resolve conflicting thresholds is absent, keep "
                "the conflict visible.\n"
                "Out of scope: Do not fail a request for a classification duty arising only "
                "after purchase; leave offer count and amount arithmetic to their respective "
                "rules.\n"
                "Verdict: fail only for a verified binding request-stage classification breach; "
                "pass only for verified compliance; not_applicable for positively excluded "
                "scope or a duty arising only later. Otherwise unknown, prefixed "
                "missing_policy, scope_unresolved, case_fact_missing or conflicting_sources.\n"
            ),
            queries={
                "de": [
                    "Beschaffung Anlagevermögen geringwertige Wirtschaftsgüter Verbrauchsmaterial Einordnung",
                    "Inventarisierung Anschaffungskosten netto brutto Beschaffungsantrag",
                    "Anlagenbuchhaltung Geräte Beschaffung Klassifizierung Wertgrenze",
                ],
                "en": [
                    "university procurement asset classification low value assets consumables",
                    "inventory capitalization purchase request net gross threshold",
                ],
            },
            questions={
                "de": [
                    "Welche Klassifikation ist für welche Beschaffungsgegenstände und Betragsgrundlagen vorgeschrieben?",
                    "Ist die Einordnung bereits im Beschaffungsantrag oder erst nach dem Kauf erforderlich?",
                ],
                "en": [
                    "Does asset classification impose a duty at the request stage?",
                ],
            },
        ),
    Rule(
            id="special_research_equipment_procedure",
            check=(
                "Subject: Review any special purchasing procedure for proposed scientific or "
                "research equipment. Identify the equipment, documented value and current "
                "request stage. Laboratory use alone does not establish coverage.\n"
                "Policy: Cite the provision specifying item and value scope, request-stage "
                "steps, responsible office and exceptions. A procedure from an equipment "
                "fund or large-device scheme applies only when case evidence establishes "
                "that scheme or its defined equipment class. A value bracket inside such "
                "a procedure is not a general purchasing threshold. A funding application "
                "procedure is not a procurement procedure.\n"
                "Compare: Establish the scheme or equipment-class link from case text "
                "before comparing its steps. Compare documented steps with binding steps "
                "already due before ordering. An ordinary laboratory device does not "
                "inherit a special scheme solely from its price or intended research use. "
                "Merely sending a request to an office does not prove that a later "
                "procedure was skipped.\n"
                "Out of scope: Exclude unrelated grant applications and duties arising only "
                "after the request. Do not use this rule as a general test for all laboratory "
                "purchases.\n"
                "Verdict: fail only for a verified binding step already due and breached; pass "
                "only for verified compliance; not_applicable if cited scope positively "
                "excludes the item or no research-equipment subject occurs. Otherwise unknown, "
                "prefixed missing_policy, scope_unresolved, case_fact_missing or "
                "conflicting_sources.\n"
            ),
            queries={
                "de": [
                    "wissenschaftliche Großgeräte Beschaffung Bestellung Sonderverfahren Hochschule",
                    "Forschungsgeräte Gerätebeschaffung Vergabeverfahren Beschaffungsstelle",
                    "wissenschaftliche Geräte Einkauf Zuständigkeit Wertgrenze",
                ],
                "en": [
                    "university scientific research equipment special procurement procedure",
                    "large research instrument purchasing procedure procurement office",
                ],
            },
            questions={
                "de": [
                    "Für welche Forschungsgeräte gilt ein besonderes Beschaffungsverfahren?",
                    "Welche Schritte sind schon vor der Bestellung im Antrag nachzuweisen?",
                ],
                "en": [
                    "Which special research-equipment duties apply to a pre-order request?",
                ],
            },
        ),
    Rule(
            id="non_eu_import_procurement",
            check=(
                "Subject: Review a purchase request involving documented import of goods from "
                "outside the EU. Identify origin and shipment route separately from supplier "
                "address, currency or brand. A non-EU seller alone does not establish a "
                "third-country import.\n"
                "Policy: Cite a binding provision defining territorial and product scope, the "
                "action due before ordering and exceptions. Separate later customs, tax and "
                "receipt duties from request-stage duties.\n"
                "Compare: Compare documented origin, route and proposed action with a quoted "
                "duty due at the request stage, taking any quoted exception into account.\n"
                "Out of scope: Do not infer import from a supplier's address alone or fail a "
                "request for a duty arising only after ordering. Leave supplier selection and "
                "invoice arithmetic to other rules.\n"
                "Verdict: fail only for a verified request-stage duty, contrary fact and no "
                "applicable exception; pass only for verified compliance; not_applicable only "
                "when the import subject does not occur or cited scope positively excludes it. "
                "Otherwise unknown, prefixed missing_policy, scope_unresolved, "
                "case_fact_missing or conflicting_sources.\n"
            ),
            queries={
                "de": [
                    "Beschaffung Einfuhr Drittland Zoll Umsatzsteuer Bestellung Hochschule",
                    "Warenimport außerhalb EU Zollabwicklung Beschaffungsstelle",
                    "Drittland Lieferung Einfuhrumsatzsteuer Forschungsgeräte",
                ],
                "en": [
                    "university purchase goods imported from outside EU customs VAT procedure",
                    "non EU supplier import origin pre-order procurement requirements",
                ],
            },
            questions={
                "de": [
                    "Wann gelten Einfuhr- und Zollvorgaben für Beschaffungen aus Drittländern?",
                    "Welche Nachweise sind bereits vor einer Bestellung erforderlich?",
                ],
                "en": [
                    "Which non-EU import duties apply before ordering, and to which goods?",
                ],
            },
        ),
]
