from src.models import Rule


# One procurement question for an isolated pilot run. Policy requirements,
# thresholds and exceptions must come from the retrieved corpus at run time.
PROCUREMENT_RULES: list[Rule] = [
    Rule(
        id="comparison_offers",
        check=(
            "1. Identify each requested item/class, procurement method, "
            "value with its tax basis, and independent offer documents. "
            "Read dated emails in order; a requested offer may arrive later.\n"
            "2. For each obligation or exception, quote its product/method "
            "scope and link it to a verbatim item/method excerpt from this "
            "case. An exception restricted to one class cannot govern "
            "unrelated products; a general offer-count default does not "
            "itself rule out a claimed direct-award method. A procedure "
            "described as available is not mandatory for every purchase.\n"
            "3. Compare the actual attached offers with an applicable quoted "
            "requirement. A claim that offers exist is not an offer document. "
            "If the claimed method is not settled by the retrieved policy, "
            "report technical unknown and identify the missing policy; "
            "do not invent approval or rejection from that gap.\n"
            "4. Fail for a proved, due requirement with fewer independent "
            "offers and no unresolved exception; pass if the applicable "
            "requirement or a quoted exception is met; not_applicable only "
            "when no currently applicable offer duty is established. "
            "For pass/fail give both a verified policy quote and a case quote. "
            "Do not judge supplier channel, arithmetic or award ranking."
        ),
        queries={
            "de": [
                "Beschaffung Vergleichsangebote Anzahl einholen Ausnahmen Rahmenvertrag",
                "Vergabe Preisvergleich schriftliche Angebote Direktauftrag Wertgrenze",
                "Beschaffungsordnung Vergabeverfahren Direktauftrag Angebote Ausnahmen",
                "Rahmenvertrag Vergleichsangebote entfallen Beschaffung",
                "Beschaffung Direktauftrag Vergleichsangebote Wertgrenze Einkauf",
            ],
            "en": [
                "university procurement comparison offers direct award exception",
                "procurement number of quotations framework agreement exemption",
            ],
        },
        questions={
            "de": [
                "Wann sind bei Beschaffungen Vergleichsangebote einzuholen, und welche Ausnahmen gelten?",
                "Wie bestimmen Auftragswert und Vergabeart die erforderlichen Angebote und Nachweise?",
                "Wann entfallen Vergleichsangebote bei Direktauftrag oder Rahmenvertrag?",
            ],
            "en": [
                "When must a procurement request include competing offers, and what exceptions apply?",
                "How do order value, direct award and framework contracts affect offer requirements?",
            ],
        },
    ),
]
