"""Isolated rule 4. Retrieval hints are not policy or numeric thresholds."""

from src.models import Rule

PROCUREMENT_RULES = [Rule(
    id="document_consistency",
    check=(
        "Review contradictions among documents attached to the pre-order "
        "request. This rule owns cross-document price transcription and "
        "identity findings, including an award note copying an offer price.\n"
        "1. Use a supplied verified document audit, if available. Check that "
        "the compared values concern the same offer, quantity and net/gross "
        "basis; an invoice may cover only part of an order. Treat the original "
        "offer price as the source for comparison with a copied price. If no "
        "audit is supplied, identify only comparisons supported by the PDFs.\n"
        "2. Cite any retrieved duty requiring consistent, accurate request "
        "information or supporting documents at this stage, with its scope "
        "and exceptions. A document discrepancy is a factual audit finding; "
        "it does not alone establish a policy breach.\n"
        "Verdict: fail only for a verified material discrepancy that breaches "
        "the cited applicable duty; pass only where that duty and the "
        "documents establish compliance; not_applicable if no comparable "
        "document subject occurs or a cited scope excludes the case. Missing "
        "or inconclusive policy or facts yields technical unknown with reason "
        "prefixed missing_policy, scope_unresolved, case_fact_missing, or "
        "conflicting_sources. Cite case and policy excerpts for pass/fail.\n"
        "Exclude offer count, framework sourcing and whether the selected "
        "offer is preferable."
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
)]
