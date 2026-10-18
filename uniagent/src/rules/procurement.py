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
            "Subject: Review each item in a pre-order purchase request for "
            "framework-contract sourcing. Identify its product class, proposed supplier and "
            "ordering channel. A catalogue entry describes the proposal; a supplier-name "
            "mismatch alone, especially with pseudonyms, does not prove a breach.\n"
            "Policy: Cite a retrieved provision that covers this product class, requires a "
            "specified framework supplier or ordering channel, and states any applicable "
            "exception. A contract for a different class is irrelevant. Treat a list marked "
            "'u.a.' as open and limit conclusions to the retrieved packet.\n"
            "Compare: Compare the proposed source and channel with that obligation at the "
            "request stage. A proposal to buy an in-scope item from a forbidden source can "
            "breach the obligation before an order is executed. For a request-stage fail, "
            "cite case text linking the in-scope item to the proposed outside supplier "
            "or channel. Read the item line, its immediately associated supplier link, "
            "and purchase language about that shop together; quote the decisive spans. "
            "Copy quantities exactly; cite each original item or shop line as a "
            "separate contiguous span, never a reconstructed item-plus-URL line. "
            "A linked shop used as the source of the requested purchase can establish "
            "a proposal even without the literal words buy from. An email addressed "
            "to procurement only sends the request; a bare product link or shop "
            "mentioned solely for price research is insufficient. Check quoted "
            "exceptions before deciding.\n"
            "Out of scope: Leave general approval workflow, offer count, price arithmetic "
            "and invoices to their own rules. Missing scope is not proof that the item is "
            "excluded.\n"
            "Verdict: fail for a verified in-scope forbidden proposal; pass only when every "
            "in-scope item is verified compliant and no item's scope remains unresolved; "
            "not_applicable only when cited scope and case evidence positively establish "
            "that no item is covered. Otherwise unknown, prefixed missing_policy, "
            "scope_unresolved or case_fact_missing as appropriate.\n"
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
