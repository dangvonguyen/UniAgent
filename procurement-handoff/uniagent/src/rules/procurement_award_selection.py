"""Rule 5 pilot. Values and item choices come from sources, not queries."""

from src.models import Rule

PROCUREMENT_RULES = [Rule(
    id="award_selection",
    check=(
        "Review the proposed award in a procurement request before ordering. "
        "First identify whether an award proposal and comparable independent "
        "offers are actually present; a request without an award note is not "
        "evidence that an award rule was violated. Recheck the selected offer ID, "
        "the original offer prices, net/gross basis, quantity and technical "
        "equivalence. Treat a price transcribed into an award table as a claim "
        "to verify against the original offer. Distinguish the case's stated "
        "selection criterion from a policy obligation: a note saying 'cheapest' "
        "does not create the legal rule. Use the retrieved policy to establish "
        "the applicable award criterion and stage, including permissible "
        "justifications for a more expensive offer. Do not assume price alone "
        "must win if the policy uses an overall value criterion. A verified "
        "mismatch is a diagnostic fact, not automatically a policy fail. Fail "
        "only for a material breach of a quoted, applicable obligation after "
        "checking an explanation or exception shown in the case. Pass only "
        "where the applicable obligation and case evidence establish "
        "compliance. If no award proposal exists, use not_applicable; if a "
        "proposal exists but governing policy is missing or inconclusive, "
        "use technical unknown. Cite short verbatim case and policy excerpts. "
        "Do not decide framework sourcing, offer-count requirements, or "
        "document arithmetic as separate rules."
    ),
    queries={
        "de": [
            "Vergabe Zuschlag wirtschaftlichstes Angebot Preis Qualität Wertung öffentliche Auftraggeber Hessen",
            "Beschaffung Universität Kassel Zuschlagsentscheidung Wertung Angebote Wirtschaftlichkeit",
            "Hessisches Vergaberecht wirtschaftlichstes Angebot Zuschlagskriterien Dokumentation",
            "Beschaffungsordnung Angebotswertung Zuschlag günstigstes geeignetes Angebot Begründung",
        ],
        "en": [
            "Hesse public procurement most economically advantageous tender award criteria university",
            "University Kassel procurement award selection price quality justification",
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
