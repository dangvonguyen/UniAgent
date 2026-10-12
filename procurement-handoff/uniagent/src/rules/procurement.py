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
            "For each requested item, identify its product class, proposed "
            "supplier and ordering channel. Link the item's class to the "
            "retrieved framework-contract scope and then cite the operative "
            "supplier/channel requirement and any exception. A contract for one "
            "class says nothing about unrelated items. A structured catalogue "
            "record is evidence of what the request claims, not proof that "
            "the contract covers the item. Pseudonymized supplier names alone "
            "cannot establish a violation. A supplier link in a request is a "
            "proposal, not an executed order; fail for a forbidden channel only "
            "if the quoted obligation attaches to this request stage or a case "
            "document proves an actual order outside the contract. Check "
            "quoted exceptions first. If any in-scope item clearly violates "
            "an applicable duty, fail. If every in-scope item complies, pass. "
            "If no item is in a positively quoted scope, not_applicable may "
            "describe only the retrieved packet; an open 'u.a.' list cannot "
            "prove global absence. If scope or obligation is unresolved, use "
            "technical unknown. Keep general ordering workflow, offer count, "
            "amounts and invoices outside this rule."
        ),
        queries={
            "de": [
                "Beschaffung Rahmenverträge verbindlich Rahmenvertragspartner Bestellung",
                "Rahmenvertrag Produkte Rahmensortiment Bezugsverpflichtung Lieferant",
                "Rahmenverträge Bestellungen WPS Katalogsystem",
                "Rahmenvertrag Beschaffung Ausnahmen Bezug",
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
