"""Isolated rule 4. Retrieval hints are not policy or numeric thresholds."""

from src.models import Rule

PROCUREMENT_RULES = [Rule(
    id="document_consistency",
    check=(
        "At the pre-order procurement-request stage, review contradictions between "
        "the request, an explicitly linked offer or catalogue cart, and any award "
        "note. First verify that the compared amounts refer to the same offer, "
        "quantity and net/gross basis; later invoices may concern only part of "
        "an order. Independently check the PDF excerpts given below. A computed "
        "discrepancy is a fact, not itself a legal violation. Identify a quoted "
        "policy obligation governing consistency, accurate price information, "
        "or required supporting documents specifically at this stage, including "
        "its conditions and exceptions. Fail only if a verified discrepancy "
        "materially breaches that obligation. Pass only if a quoted applicable "
        "obligation is satisfied and the relevant documents can be compared. "
        "Use not_applicable when this rule's subject does not occur; use technical "
        "unknown if relevant documents or governing policy are unavailable. "
        "Do not decide whether enough offers were requested, whether the selected "
        "offer is best, or whether a framework contract applies. Cite verbatim "
        "PDF and policy excerpts for pass/fail. Keep the reason short."
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
