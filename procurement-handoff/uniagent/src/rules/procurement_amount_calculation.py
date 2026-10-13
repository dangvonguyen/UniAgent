"""Isolated procurement rule 3; policy values come only from retrieved sources."""

from src.models import Rule


PROCUREMENT_RULES: list[Rule] = [
    Rule(
        id="amount_calculation",
        check=(
            "Review request-stage monetary obligations, using any verified "
            "arithmetic audit supplied with the case as factual input.\n"
            "1. Identify the audited operands, document excerpts and net/gross "
            "basis. If an audit is supplied, do not independently invent or "
            "replace its calculations. If none is supplied, report which "
            "amounts are stated without assuming an unstated VAT rate, "
            "discount, or missing table row. Keep each document separate.\n"
            "2. Cite a retrieved obligation governing the request-stage amount "
            "or supporting calculation, including scope and any exception. "
            "Do not infer a tolerance or threshold from another category.\n"
            "Verdict: fail only if the verified facts materially breach that "
            "applicable obligation; pass only if the quoted duty and verified "
            "facts establish compliance; not_applicable only if there is no "
            "monetary subject or a cited scope positively excludes the case. "
            "If the obligation or amount basis is missing or ambiguous, return "
            "technical unknown with reason prefixed missing_policy, "
            "scope_unresolved, case_fact_missing, or conflicting_sources. "
            "Keep any arithmetic anomaly in the audit even without a policy "
            "verdict.\n"
            "Do not decide whether two different documents refer to the same "
            "offer (document_consistency), whether the selected offer is the "
            "best one (award_selection), or whether enough offers were sought."
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
