from src.models import Rule


# One procurement question for an isolated pilot run. Policy requirements,
# thresholds and exceptions must come from the retrieved corpus at run time.
PROCUREMENT_RULES: list[Rule] = [
    Rule(
        id="comparison_offers",
        check=(
            "Assess comparison offers only. Follow this order:\n"
            "1. Identify the requested goods or services, the stated method "
            "(including a claimed direct award or framework call-off), the "
            "order value and its currency/tax basis, and all independent "
            "supplier offers in the submitted documents. Read dated emails "
            "chronologically; a requested offer may arrive later.\n"
            "2. Cite policy establishing the offer requirement for this "
            "method and product scope, with its conditions and exceptions. "
            "A general 'normally three offers' statement establishes a "
            "default; it does not by itself prove every claimed direct-award "
            "exception is forbidden. A threshold or exception for one category "
            "does not govern another category. A procedure described as "
            "possible is not mandatory for every purchase.\n"
            "3. If the case claims direct award and the quoted policy does "
            "not settle whether that method is permitted for these items "
            "and this value, choose unknown and name the missing policy. "
            "Neither assume the applicant's exception is valid nor assert "
            "that it is forbidden without an applicable quote.\n"
            "4. Fail only when an applicable quoted requirement establishes "
            "the necessary offers and the complete submitted packet shows "
            "fewer independent offers, with no unresolved exception. Pass "
            "when the applicable requirement is met or a quoted exception "
            "is shown to apply. Do not use not_applicable to hide missing "
            "policy. A statement about offers is not an offer document.\n"
            "Do not judge framework supplier/channel, price arithmetic or "
            "award ranking under this rule."
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
