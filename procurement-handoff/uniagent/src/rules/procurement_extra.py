"""Four candidate procurement rules registered beside the five existing rules.

These definitions require source-backed checks at runtime. Do not treat their
presence in the rule list as proof of retrieval coverage or case accuracy.
"""

from src.models import Rule


EXTRA_PROCUREMENT_RULES: list[Rule] = [
    Rule(
        id="request_and_order_authority",
        check=(
            "Review authority at the pre-order request stage.\n"
            "1. Identify the requester, proposed approver, signatures and any "
            "documented delegation. Distinguish request approval from the "
            "later act of placing an order.\n"
            "2. Cite a binding provision stating who may request, approve or "
            "order, and when, with applicable delegation or exceptions. An "
            "organizational task list does not alone impose a mandatory "
            "request-stage approval.\n"
            "Verdict: fail for a verified breach of a duty already due; pass "
            "for verified compliance with that duty; not_applicable only if "
            "the subject does not occur or cited scope excludes the case. A "
            "blank field for a later stage is not a request-stage failure. "
            "Unresolved authority, timing or missing policy gives technical "
            "unknown with reason prefixed missing_policy, scope_unresolved, "
            "case_fact_missing, or conflicting_sources."
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
            "Review classification of the requested item at the pre-order "
            "stage.\n"
            "1. Identify each item's nature, quantity, stated amount and "
            "net/gross basis from the case or verified audit.\n"
            "2. Cite a binding provision for the item's classification, its "
            "threshold and tax basis, and whether it applies at the request "
            "stage. When sources disagree, report each source's title, issuer "
            "and effective or publication date if supplied; never resolve "
            "authority or recency from memory or an excerpt without metadata. "
            "Do not assume a VAT rate or threshold.\n"
            "Verdict: fail only for a verified breach of a binding request-stage "
            "classification duty; pass only for verified compliance; "
            "not_applicable if a cited scope excludes the item or the cited "
            "duty arises only later. Missing source, amount basis or metadata "
            "needed to resolve conflicting thresholds yields technical unknown "
            "with reason prefixed missing_policy, case_fact_missing, or "
            "conflicting_sources."
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
            "Review any special purchase procedure for research equipment.\n"
            "1. Identify the proposed equipment, its documented value and the "
            "current request stage. A laboratory item alone does not establish "
            "coverage by a special procedure.\n"
            "2. Cite the procurement provision defining the item and value "
            "scope, the request-stage steps, responsible office and exceptions. "
            "A funding application process is not a purchase procedure. "
            "A request sent to an office does not prove a later step was "
            "skipped.\n"
            "Verdict: fail only for a verified binding step already due and "
            "breached; pass for verified compliance; not_applicable if a "
            "cited scope positively excludes the item or no equipment subject "
            "occurs. Otherwise return technical unknown with reason prefixed "
            "missing_policy, scope_unresolved, case_fact_missing, or "
            "conflicting_sources."
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
            "Review import duties applicable to the pre-order request.\n"
            "1. Identify the documented origin and route of goods separately "
            "from supplier address, currency or brand. A supplier outside the "
            "EU alone does not prove a third-country import.\n"
            "2. Cite the territorial and product scope of a binding provision, "
            "the action due before ordering, and exceptions. Separate later "
            "customs, tax and receipt duties from request-stage duties.\n"
            "Verdict: fail only for a verified request-stage duty and contrary "
            "fact with no applicable exception; pass for verified compliance; "
            "not_applicable only if the import subject does not occur or a "
            "cited scope positively excludes it. Missing origin or policy "
            "gives technical unknown with reason prefixed missing_policy, "
            "scope_unresolved, case_fact_missing, or conflicting_sources."
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
