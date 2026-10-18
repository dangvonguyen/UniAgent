"""Isolated rule 4. Retrieval hints are not policy or numeric thresholds."""

from src.models import Rule

PROCUREMENT_RULES = [Rule(
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
)]
