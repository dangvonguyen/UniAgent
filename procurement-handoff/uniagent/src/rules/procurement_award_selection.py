"""Rule 5 pilot. Values and item choices come from sources, not queries."""

from src.models import Rule

PROCUREMENT_RULES = [Rule(
    id="award_selection",
    check=(
        "Review the proposed selection among offers before ordering.\n"
        "1. Identify the proposal, comparable independent offers, and the "
        "case's stated criterion. A missing award note alone is not a breach. "
        "Use any verified document audit for offer identity and original "
        "prices; leave copied-price contradictions to document_consistency.\n"
        "2. Cite a retrieved, stage-applicable selection obligation and its "
        "exceptions. Separate the applicant's stated criterion from that "
        "obligation. A duty to announce criteria does not establish that the "
        "lowest price must win; evaluate quality and permitted justifications "
        "where the applicable policy requires them.\n"
        "Verdict: fail only if the proposed selection materially breaches "
        "the cited criterion with no supported justification or exception; "
        "pass only if the quoted obligation and case facts establish "
        "compliance; not_applicable if no selection among offers is proposed "
        "or a cited scope excludes this request. If the relevant criterion "
        "or comparison facts cannot be established, return technical unknown "
        "with reason prefixed missing_policy, scope_unresolved, "
        "case_fact_missing, or conflicting_sources. Cite short case and "
        "policy excerpts for pass/fail.\n"
        "Exclude framework sourcing, offer-count requirements and separate "
        "document arithmetic."
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
)]
