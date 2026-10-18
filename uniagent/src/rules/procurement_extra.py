"""Four candidate procurement rules registered beside the five existing rules.

These definitions require source-backed checks at runtime. Do not treat their
presence in the rule list as proof of retrieval coverage or case accuracy.
"""

from src.models import Rule


EXTRA_PROCUREMENT_RULES: list[Rule] = [
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
