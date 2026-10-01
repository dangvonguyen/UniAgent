from .models import Rule

# Queries are BM25 keyword bags fused by reciprocal rank, so each rule gets several
# short queries, one per facet , instead of one long query that dilutes every term.
# Questions are natural-language questions the policy text answers, for dense retrieval
# and reranking, which match sentences rather than keywords.

RULES: list[Rule] = [
    Rule(
        id="trip_approval",
        check=(
            "Business-trip approval: compare when and by whom the trip was applied "
            "for and approved with the trip dates, against the policy's requirements "
            "on approval of business trips, including any exceptions."
        ),
        queries={
            "de": [
                "Dienstreise Genehmigung Anordnung",
                "Dienstreise Genehmigung Form schriftlich elektronisch",
                "Dienstreise Genehmigung Ausnahme nachträglich",
                "Dienstreise Genehmigung Ausnahme Amt Funktion",
                "Dienstreise Genehmigung Zuständigkeit Vorgesetzte Dienststelle",
            ],
            "en": [
                "business trip approval authorisation",
                "business trip approval exception retroactive",
            ],
        },
        questions={
            "de": [
                "Wer muss eine Dienstreise genehmigen oder anordnen, und in welcher Form?",
                "Kann eine Dienstreise auch nachträglich genehmigt werden?",
                "Für wen ist keine Genehmigung einer Dienstreise erforderlich?",
            ],
            "en": [
                "Who approve a business trip, and in what form?",
                "Are there exceptions to the approval requirement for business trips?",
            ],
        },
    ),
    Rule(
        id="expense_claim_submission",
        check=(
            "Expense claim submission: compare when and how the travel-expense claim "
            "was submitted, relative to the end of the trip, against the policy's "
            "requirements on claiming travel expenses, including any exceptions."
        ),
        queries={
            "de": [
                "Reisekostenvergütung Antrag Ausschlussfrist",
                "Reisekostenabrechnung Einreichung Frist Beendigung Dienstreise",
                "Reisekostenvergütung Ausschlussfrist Beendigung Dienstreise beantragen",
            ],
            "en": [
                "travel expense claim submission deadline",
                "travel expense claim time limit end of trip",
            ],
        },
        questions={
            "de": [
                "Innerhalb welcher Frist muss die Reisekostenvergütung beantragt werden?",
                "Welche Folgen hat eine verspätete Reisekostenabrechnung?",
                "Wie und wo wird die Reisekostenabrechnung eingereicht?",
            ],
            "en": [
                "By when must a travel expense claim be submitted after the trip ends?",
                "What happens if a travel expense claim is submitted late?",
            ],
        },
    ),
    Rule(
        id="accommodation_costs_domestic",
        check=(
            "Domestic accommodation costs: compare the case's overnight "
            "accommodation costs for a trip within the country against the policy's "
            "reimbursement rule for domestic overnight costs, including any "
            "conditions, justification clauses and exceptions."
        ),
        queries={
            "de": [
                "Übernachtungskosten Dienstreise Inland Erstattung",
                "Übernachtungsgeld Übernachtungskosten Hotel Erstattung",
                "Übernachtungskosten Begründung Nachweis Ausnahme",
            ],
            "en": [
                "domestic business trip accommodation overnight costs reimbursement",
                "overnight allowance hotel costs reimbursement",
                "accommodation costs justification evidence exception",
            ],
        },
        questions={
            "de": [
                "Welche Übernachtungskosten werden bei Dienstreisen im Inland erstattet?",
                "Unter welchen Voraussetzungen werden Übernachtungskosten erstattet?",
                "Welche Ausnahmen gelten für die Erstattung von Übernachtungskosten?",
            ],
            "en": [
                "Which hotel costs are reimbursed for overnight stays on domestic business trips?",
                "Under what conditions are accommodation costs reimbursed?",
            ],
        },
    ),
    Rule(
        id="accommodation_costs_abroad",
        check=(
            "Foreign accommodation costs: compare the case's overnight accommodation "
            "costs for a trip abroad, and the destination country, against the "
            "policy's reimbursement rule for overnight costs abroad, including any "
            "conditions, justification clauses and exceptions."
        ),
        queries={
            "de": [
                "Auslandsdienstreise Übernachtungskosten Erstattung",
                "Auslandsdienstreisen Auslandstagegeld Auslandsübernachtungsgeld",
                "Auslandsdienstreise Übernachtungskosten Begründung Nachweis Ausnahme",
                "Auslandsdienstreise Begriff Ausland Inland Dienstreise",
                "Auslandsübernachtungsgeld Übernachtungskosten notwendig",
            ],
            "en": [
                "business trip abroad accommodation overnight costs reimbursement",
                "foreign travel overnight allowance country",
            ],
        },
        questions={
            "de": [
                "Welche Übernachtungskosten werden bei Auslandsdienstreisen erstattet?",
                "Wie wird das Auslandsübernachtungsgeld bemessen?",
            ],
            "en": [
                "Which accommodation costs are reimbursed for business trips abroad?",
                "How is the overnight allowance for travel abroad determined?",
            ],
        },
    ),
    Rule(
        id="business_private_trip_combination",
        check=(
            "Combining business and private travel: compare any private days, "
            "private stay or private detour in the case against the policy's rules "
            "on business trips combined with private travel, including notification, "
            "cost allocation and exceptions."
        ),
        queries={
            "de": [
                "Verbindung Dienstreise private Reise",
                "Dienstreise Urlaub Verbindung Reisekostenvergütung",
                "Dienstreise Privataufenthalt private Verlängerung",
                "Dienstreise Urlaub Reiseweg Fahrtkosten",
            ],
            "en": [
                "business trip combined with private travel vacation",
                "business trip private stay extension",
            ],
        },
        questions={
            "de": [
                "Wie werden Reisekosten erstattet, wenn eine Dienstreise mit einem Urlaub oder einer privaten Reise verbunden wird?",
                "Was gilt, wenn Beschäftigte vor oder nach der Dienstreise privat am Reiseziel bleiben?",
                "Muss ein privater Reiseteil angezeigt oder genehmigt werden?",
            ],
            "en": [
                "How are travel costs reimbursed when a business trip is combined with a holiday or private travel?",
                "Must the private part of a combined trip be reported or approved?",
            ],
        },
    ),
    Rule(
        id="cross_border_social_security_coverage",
        check=(
            "Social-security coverage for work abroad: compare the case's "
            "destination, trip dates and any social-security certificate or its "
            "application against the policy's requirements for such certificates, "
            "including scope, timing and exceptions."
        ),
        queries={
            "de": [
                "A1 Bescheinigung Sozialversicherung Ausland",
                "Entsendebescheinigung Antrag Auslandsdienstreise",
                "A1 Bescheinigung beantragen rechtzeitig vor Reiseantritt",
                "Auslandsdienstreise Sozialversicherung Krankenversicherung Ausland",
            ],
            "en": [
                "A1 certificate social security abroad",
                "A1 certificate application business trip abroad",
            ],
        },
        questions={
            "de": [
                "Wann wird für eine Dienstreise ins Ausland eine A1-Bescheinigung benötigt, und wie wird sie beantragt?",
                "Wie und wann wird eine A1-Bescheinigung beantragt?",
                "Für welche Länder ist eine Entsendebescheinigung erforderlich?",
            ],
            "en": [
                "When is an A1 social security certificate required for a business trip abroad, and how is it applied for?",
            ],
        },
    ),
    Rule(
        id="transport_costs",
        check=(
            "Transport costs: compare the case's means of transport, travel class "
            "and fares against the policy's rules on reimbursable transport costs, "
            "including any justification clauses and exceptions."
        ),
        queries={
            "de": [
                "Fahrtkosten Flugkosten Erstattung",
                "regelmäßig verkehrendes Beförderungsmittel Beförderungsklasse",
                "Beförderungsklasse Ausnahme Begründung Erstattung",
                "Bahnfahrt Klasse Dienstreise",
                "Flugreise Dienstreise Kosten Bahnfahrt",
            ],
            "en": [
                "transport costs class of travel reimbursement",
                "business trip flight train choice",
            ],
        },
        questions={
            "de": [
                "Welche Fahrtkosten für öffentliche Verkehrsmittel werden bei Dienstreisen erstattet?",
                "Welche Beförderungsklasse ist erstattungsfähig?",
                "Wann werden Flugkosten erstattet?",
                "Wie werden Kosten für ein privates Kraftfahrzeug, Taxi oder Mietwagen erstattet?",
            ],
            "en": [
                "Which travel class is reimbursed for train or air travel on business trips?",
                "When are flight costs reimbursed?",
                "How are private car, taxi or rental car costs reimbursed?",
            ],
        },
    ),
    Rule(
        id="invoice_formalities",
        check=(
            "Invoice and receipt formalities: compare the case's invoices and "
            "receipts (addressee, issuer, itemisation, originals) against the "
            "policy's requirements on documenting travel expenses, including any "
            "exceptions."
        ),
        queries={
            "de": [
                "Rechnung Rechnungsempfänger Rechnungsanschrift",
                "Reisekosten Belege Nachweis Kostennachweise",
                "Belege Reisekostenabrechnung beifügen vorlegen",
                "Rechnung ausgestellt auf Name Dienststelle",
                "Hotelrechnung Rechnungsempfänger Dienstreise",
            ],
            "en": [
                "invoice addressee billing address",
                "travel expenses receipts proof",
            ],
        },
        questions={
            "de": [
                "Welche Belege müssen der Reisekostenabrechnung beigefügt werden?",
                "Auf wen müssen Rechnungen für Dienstreisen ausgestellt sein?",
                "Was gilt, wenn ein Beleg fehlt oder verloren gegangen ist?",
            ],
            "en": [
                "Which receipts must be submitted with a travel expense claim?",
                "What applies if a receipt is missing or lost?",
            ],
        },
    ),
    Rule(
        id="event_side_program_costs",
        check=(
            "Event side-programme costs: compare any costs in the case for social, "
            "cultural or accompanying parts of an event against the policy's rules "
            "on which event-related costs are reimbursable, including any exceptions."
        ),
        queries={
            "de": [
                "Rahmenprogramm Begleitprogramm Veranstaltung Kosten",
                "Bewirtung Veranstaltung Kosten Erstattung",
                "Teilnahmegebühr Tagung Verpflegung Mahlzeiten",
                "Veranstaltung Mahlzeiten Teilnahmegebühr Erstattung",
            ],
            "en": [
                "side programme accompanying programme event costs",
                "conference fee includes meals",
            ],
        },
        questions={
            "de": [
                "Welche Kosten einer Tagung werden erstattet, etwa Teilnahmegebühren?",
                "Werden Kosten für ein Rahmenprogramm oder Ausflüge bei Tagungen erstattet?",
                "Wie werden im Tagungsbeitrag enthaltene Mahlzeiten berücksichtigt?",
            ],
            "en": [
                "Which conference costs are reimbursed, such as fees, included meals or social programme?",
                "How are meals included in a conference fee treated?",
            ],
        },
    ),
    Rule(
        id="third_party_funding",
        check=(
            "Third-party funding: compare any costs in the case that are covered, "
            "paid or reimbursed by another party against the policy's rules on "
            "travel costs borne by third parties, including any exceptions."
        ),
        queries={
            "de": [
                "Reisekosten Kostenübernahme Dritte Anrechnung",
                "Leistungen dritter Seite Reisekostenvergütung",
                "Drittmittelprojekt Dienstreise Zuwendungsgeber",
                "Dienstreise Kosten von anderer Stelle erstattet",
                "Drittmittelgeber Bestimmungen Reisekosten Dienstreise",
            ],
            "en": [
                "travel costs covered by third party offset",
                "third-party funding travel costs reimbursement",
            ],
        },
        questions={
            "de": [
                "Wie werden Leistungen von dritter Stelle auf die Reisekostenvergütung angerechnet?",
                "Welche Bestimmungen gelten für Dienstreisen, die aus Drittmitteln finanziert werden?",
            ],
            "en": [
                "How are travel costs that are paid by a third party or a funder treated in the reimbursement?",
                "Which rules apply to business trips funded by third-party grants?",
            ],
        },
    ),
]
