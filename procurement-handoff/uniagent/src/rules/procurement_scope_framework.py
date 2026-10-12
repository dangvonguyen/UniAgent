from src.models import Rule


# First procurement pilot: one question, with every obligation supplied by
# retrieved policy quotes at run time. Do not add values or named vendors here.
PROCUREMENT_RULES: list[Rule] = [
    Rule(
        id="framework_contract_sourcing",
        check=(
            "1. For each requested item, identify its product class, proposed "
            "supplier and ordering channel from a verbatim case excerpt.\n"
            "2. Cite the policy scope that covers that product class, then its "
            "supplier/channel obligation and every relevant exception. A "
            "contract for one class does not govern unrelated goods. A list "
            "marked u.a. is open: lack of a matching retrieved quote cannot "
            "establish that no contract exists. A catalogue record shows what "
            "the case used, not that a contract governs that item.\n"
            "3. Determine the stage. A webshop link in an email requesting "
            "purchase is a proposal, not an executed order. If the quoted "
            "obligation concerns ordering and this packet only requests a "
            "future order, it is not yet due at this decision stage. Fail only "
            "if the quoted duty applies at this request stage or a case "
            "document proves a completed purchase outside the contract, and "
            "no quoted exception applies. A name mismatch alone may reflect "
            "pseudonymization; it is not proof of violation.\n"
            "4. Aggregate across items: fail for at least one proved in-scope "
            "breach; pass when every in-scope item meets a currently due "
            "quoted duty; not_applicable when no currently due in-scope duty "
            "is established. For absence, say only that the retrieved quotes "
            "do not establish scope for the cited items; cite a relevant "
            "scope quote and the case item. Never claim that no contract "
            "exists merely from search absence.\n"
            "Do not judge comparison offers, totals, invoices or general "
            "ordering workflow here."
        ),
        queries={
            "de": [
                "Beschaffung Rahmenverträge verbindlich Rahmenvertragspartner Bestellung",
                "Rahmenvertrag Produkte Rahmensortiment Bezugsverpflichtung Lieferant",
                "Rahmenverträge Bestellungen WPS Katalogsystem",
                "Rahmenvertrag Beschaffung Ausnahmen Bezug",
                "Rahmenvereinbarung Produktgruppen Beschaffung Bezugsverpflichtung",
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
