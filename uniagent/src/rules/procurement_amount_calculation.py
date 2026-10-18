"""Isolated procurement rule 3; policy values come only from retrieved sources."""

from src.models import Rule


PROCUREMENT_RULES: list[Rule] = [
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
]
