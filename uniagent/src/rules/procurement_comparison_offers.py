from src.models import Rule


# One procurement question for an isolated pilot run. Policy requirements,
# thresholds and exceptions must come from the retrieved corpus at run time.
PROCUREMENT_RULES: list[Rule] = [
    Rule(
        id="comparison_offers",
        check=(
            "Subject: Review the number of independent comparison offers submitted for the "
            "proposed purchase. Identify the goods or services, stated procurement method, "
            "value and tax basis, and actual offer documents. Read dated emails in order; a "
            "later response can supply an offer.\n"
            "Policy: Cite the applicable offer requirement, its product and method scope, "
            "value basis and exceptions, including direct award or framework call-off. A "
            "general default does not settle an exception. A merely possible procedure is "
            "not mandatory for every purchase; a pointer to another rule does not provide "
            "that missing rule.\n"
            "Compare: Count independent offers evidenced by submitted offer documents "
            "rather than a stated count. Match each threshold and exception to the case's "
            "goods or services, method and value basis. If a direct-award claim cannot be "
            "assessed with the retrieved policy, report the missing provision instead of "
            "presuming the exception valid or invalid.\n"
            "Out of scope: Leave framework supplier and channel, arithmetic and award "
            "ranking to their own rules. Do not treat missing policy as proof of "
            "non-applicability.\n"
            "Verdict: fail only when an applicable quoted duty requires more offers than "
            "the complete packet shows and no exception remains unresolved; pass only when "
            "the requirement or a quoted exception is verified. Use not_applicable only for "
            "positively established exclusion. Otherwise unknown, prefixed missing_policy, "
            "scope_unresolved, case_fact_missing or conflicting_sources.\n"
        ),
        queries={
            "de": [
                "Beschaffung Vergleichsangebote Anzahl einholen Ausnahmen Rahmenvertrag",
                "Vergabe Preisvergleich schriftliche Angebote Direktauftrag Wertgrenze",
                "Beschaffungsordnung Vergabeverfahren Direktauftrag Angebote Ausnahmen",
                "Rahmenvertrag Vergleichsangebote entfallen Beschaffung",
                "Beschaffung Direktauftrag Vergleichsangebote Wertgrenze Einkauf",
                "Beschaffungsordnung Direktvergabe Direktkauf Beschaffungswert ohne Vergleichsangebote",
                "drei Angebote grundsätzlich Ausnahmen Direktauftrag Vergabeverfahren",
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
                "Enthält die Fundstelle selbst eine Wertgrenze samt Geltungsbereich, oder verweist sie nur auf eine andere Ordnung?",
            ],
            "en": [
                "When must a procurement request include competing offers, and what exceptions apply?",
                "How do order value, direct award and framework contracts affect offer requirements?",
            ],
        },
    ),
]
