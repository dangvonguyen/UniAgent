"""Rule 5 pilot. Values and item choices come from sources, not queries."""

from src.models import Rule

PROCUREMENT_RULES = [Rule(
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
)]
