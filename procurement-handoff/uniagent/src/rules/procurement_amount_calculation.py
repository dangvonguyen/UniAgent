"""Isolated procurement rule 3; policy values come only from retrieved sources."""

from src.models import Rule


PROCUREMENT_RULES: list[Rule] = [
    Rule(
        id="amount_calculation",
        check=(
            "Review material arithmetic and the stated monetary basis of this "
            "procurement request at its current pre-order stage. Follow these steps:\n"
            "1. Identify line quantities, unit prices, discounts, shipping, "
            "tax amounts or rates, and stated net/gross subtotals and totals. "
            "Keep each document's prices and tax basis separate.\n"
            "2. Recompute only equations supported by the case text. Explain "
            "which operands and tax basis were used. Do not assume an unstated "
            "tax rate, a hidden discount, or that an estimate, offer and later "
            "invoice must have identical totals.\n"
            "3. Compare a supported discrepancy with retrieved policy covering "
            "this request and stage. Cite the applicable source, its scope and "
            "whether it requires a correct amount or evidence at this stage. "
            "Do not invent a tolerance or monetary threshold.\n"
            "4. Fail only for a material, demonstrated breach of that quoted "
            "obligation. Pass if the in-scope calculations satisfy it. Use "
            "not_applicable only if the case has no monetary calculation to "
            "assess; if the policy is missing or ambiguous, use the technical "
            "unknown verdict and explain what source is missing.\n"
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
