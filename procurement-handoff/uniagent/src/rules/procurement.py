from src.models import Rule

from .procurement_comparison_offers import PROCUREMENT_RULES as COMPARISON_OFFERS
from .procurement_amount_calculation import PROCUREMENT_RULES as AMOUNT_CALCULATION
from .procurement_document_consistency import PROCUREMENT_RULES as DOCUMENT_CONSISTENCY
from .procurement_award_selection import PROCUREMENT_RULES as AWARD_SELECTION


# Five separate subjects; policy obligations come from the retrieved corpus.
PROCUREMENT_RULES: list[Rule] = [
    Rule(
        id="framework_contract_sourcing",
        check=(
            "Review the proposed purchase at the pre-order request stage.\n"
            "1. For each item, identify its product class, proposed supplier "
            "and ordering channel from the case. A catalogue record describes "
            "the proposal; a supplier-name mismatch alone, especially with "
            "pseudonyms, does not prove a breach.\n"
            "2. Cite a retrieved provision placing that product class within "
            "a binding framework contract, its supplier/channel obligation, "
            "and any applicable exception. A contract for another class is "
            "irrelevant. If the cited list says 'u.a.', state that it is open; "
            "limit conclusions to the retrieved packet.\n"
            "3. The request is the decision under review: a proposal to buy "
            "an in-scope item from a source that the cited obligation forbids "
            "can fail before an order is executed. Verify that the proposed "
            "source is actually forbidden and that no quoted exception applies. "
            "A bare product link without an identified intended supplier or "
            "channel is insufficient.\n"
            "Verdict: fail if any in-scope proposed item clearly breaches the "
            "cited obligation; pass if every in-scope proposed item complies; "
            "not_applicable only when cited policy scope and case evidence "
            "positively establish that no item is covered. If the packet does not establish "
            "scope or obligation, return technical unknown and prefix the "
            "reason with missing_policy or scope_unresolved. An open list or "
            "an unsuccessful search cannot prove exclusion.\n"
            "Exclude general approval workflow, offer count, price arithmetic "
            "and invoices."
        ),
        queries={
            "de": [
                "Beschaffung Rahmenverträge verbindlich Rahmenvertragspartner Bestellung",
                "Rahmenvertrag Produkte Rahmensortiment Bezugsverpflichtung Lieferant",
                "Rahmenverträge Bestellungen WPS Katalogsystem",
                "Rahmenvertrag Beschaffung Ausnahmen Bezug",
                "Rahmenvertrag Produktgruppen Sortiment Beschaffungsgegenstände Bezugsweg",
                "Rahmenvereinbarung Bezugsverpflichtung Produktgruppen Lieferweg Ausnahmen",
            ],
            "en": [
                "university procurement mandatory framework agreement supplier ordering",
                "framework contract catalogue order channel exceptions",
            ],
        },
        questions={
            "de": [
                "Für welche Beschaffungsgegenstände gelten verbindliche Rahmenverträge, und wie sind diese zu beziehen?",
                "Welche Vertragspartner und Bestellsysteme gelten für Produkte eines Rahmenvertrags?",
                "Welche produktspezifischen Absätze folgen einer nur beispielhaften Liste (u.a.)?",
                "Welche Ausnahmen oder Einschränkungen gelten für den Bezug über Rahmenverträge?",
            ],
            "en": [
                "Which purchases must use a framework contract and its supplier or ordering system?",
                "What scope limits or exceptions apply to framework-contract sourcing?",
            ],
        },
    ),
]

PROCUREMENT_RULES.extend(
    COMPARISON_OFFERS + AMOUNT_CALCULATION + DOCUMENT_CONSISTENCY + AWARD_SELECTION
)

# BEGIN UniAgent four procurement candidate rules
from .procurement_extra import EXTRA_PROCUREMENT_RULES as _EXTRA_PROCUREMENT_RULES
PROCUREMENT_RULES.extend(_EXTRA_PROCUREMENT_RULES)
# END UniAgent four procurement candidate rules
