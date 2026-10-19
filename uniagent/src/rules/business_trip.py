from src.models import Rule

# Queries are BM25 keyword bags fused by reciprocal rank, so each rule gets several
# short queries, one per facet , instead of one long query that dilutes every term.
# Questions are natural-language questions the policy text answers, for dense retrieval
# and reranking, which match sentences rather than keywords.

BUSINESS_TRIP_RULES: list[Rule] = [
    Rule(
        id="trip_approval",
        check=(
            (
            (
            (
            (
            'Subject: Timely application for and authorization of the business trip at the stage shown by the submitted dossier.\n'
            "Policy: Distinguish submitting an application for approval from receiving completed authorization. Identify which step is mandatory at the present stage and the policy's actual deadline.\n"
            'Compare: Use the application date, travel start date, workflow status and any actual authorization record. An application with status "submitted" or "pending" and an empty approval field is awaiting a decision; this does not itself establish that travel took place without approval. An applicant\'s signature is not the supervisor\'s approval. Check whether the request was submitted before travel and whether approval is demonstrably overdue or travel already commenced without required authorization. Apply the same stage rule to all applicants, regardless of event, destination or outcome label.\n'
            'Out of scope: Filing a later travel-expense claim, A1/E101 certification and funding offsets.\n'
            'Verdict: Fail for a proven late application or an authorization requirement shown to be violated when due. Pass a timely pre-trip submission still awaiting an approval that is not yet due at submission; this does not assert that final approval has been granted. Unknown if the status or timing needed to decide a due requirement is genuinely unresolved. Do not fail solely because a pending request lacks a completed approver signature.'
        )
        )
        )
        )
        ),
        queries={'de': [
                           'Dienstreise Genehmigung Anordnung',
                           'Dienstreise Genehmigung Form schriftlich elektronisch',
                           'Dienstreise Genehmigung Ausnahme nachträglich',
                           'Dienstreise Genehmigung Ausnahme Amt Funktion',
                           'Dienstreise Genehmigung Zuständigkeit Vorgesetzte Dienststelle',
                           'SAP ESS Dienstreisemanagement Dienstreiseantrag Workflow Genehmigung',
                           'FIORI Dienstreiseantrag senden zur Genehmigung mehrstufiges Verfahren',
                           'Dienstreisemanagement Alle Anträge vollständig auszufüllen',
                       ], 'en': ['business trip approval authorisation', 'business trip approval exception retroactive']},
        questions={'de': [
                             'Wer muss eine Dienstreise genehmigen oder anordnen, und in welcher Form?',
                             'Kann eine Dienstreise auch nachträglich genehmigt werden?',
                             'Für wen ist keine Genehmigung einer Dienstreise erforderlich?',
                             'Wie verläuft die Genehmigung eines in SAP ESS eingereichten Dienstreiseantrags, und ab wann darf die Reise angetreten werden?',
                             'Welche Angaben und Unterlagen muss ein Dienstreiseantrag vor Reisebeginn enthalten?',
                         ], 'en': ['Who approve a business trip, and in what form?', 'Are there exceptions to the approval requirement for business trips?']},
    ),
    Rule(
        id="expense_claim_submission",
        check=(
            (
            'Subject: Submission of an actual travel-expense reimbursement claim after travel, including its filing deadline and route.\n'
            'Policy: Retrieve the rule on Reisekostenabrechnung or Reisekostenvergütung and its deadline measured from the trip end, with any exceptions.\n'
            'Compare: First establish whether a reimbursement claim was actually filed. An Antrag auf Dienstreisegenehmigung, including estimated costs requested for approval, is a different workflow. Only for an actual claim compare its submission date and route with the trip end and policy.\n'
            'Out of scope: Pre-trip approval requests, estimated budgets, and whether future invoices will support a later claim.\n'
            'Verdict: Not_applicable when the dossier contains no actual travel-expense claim. Fail only when an actual claim violates a requirement that applies to it. Pass a timely compliant claim; unknown if material policy or claim facts are unresolved.'
        )
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
            (
            'Subject: Domestic overnight accommodation costs requested for the business portion of a trip.\n'
            'Policy: Identify the applicable domestic overnight allowance, actual-cost conditions, justification thresholds and exceptions; do not import a rule for another country or payment stage.\n'
            'Compare: Check destination, nights, rate, purpose and any required justification. Distinguish estimated accommodation in a pre-trip request from accommodation already incurred and claimed for reimbursement. Require a final hotel receipt only when the governing provision requires it at the present stage.\n'
            'Out of scope: Foreign stays, general invoice addressee defects, and the later claim-submission deadline.\n'
            'Verdict: Not_applicable without domestic accommodation. Fail for a supported breach of an applicable rate or documentation duty already due. Pass when the present-stage conditions are met; unknown if the relevant rate or facts cannot be established.'
        )
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
            (
            'Subject: Foreign overnight accommodation costs requested for the business portion of a trip.\n'
            "Policy: Apply the foreign overnight provision for the destination country. Its actual-cost ceiling is the amount set by the applicable foreign-travel schedule for that country. A domestic fixed euro limit in another passage is not this country amount, even when the passages occur together. Keep the no-proof flat allowance for a completed reimbursement claim separate from a planned nightly estimate. Do not infer an absent country rate from a domestic limit or from the applicant's assertion.\n"
            "Compare: Establish whether this is a pre-trip application with estimated cost or a post-trip reimbursement claim. An estimate is not an election of the no-proof flat allowance, and no final hotel receipt is due before the stay. Evaluate any necessity justification due when applying. Compare an amount against the destination-country schedule only if that country's numeric amount is present in the policy evidence; the applicant's statement that a rate is within the limit is a claim to verify, not independent proof of the limit.\n"
            'Out of scope: General invoice formalities, trip approval and privately paid portions.\n'
            'Verdict: Not_applicable without foreign accommodation. Fail only for a demonstrated breach of a binding amount or requirement due now. Pass only if the applicable amount and present-stage requirements can actually be checked and are met. If the foreign country rate needed for that comparison is missing from the retrieved policy, return unknown and say which rate is missing; never substitute a domestic rate or accept an unverified compliance claim. Do not reject a pre-trip estimate for lacking a future receipt or for exceeding the later no-proof allowance.'
        )
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
            (
            'Subject: Allocation of travel costs when business travel is combined with private days, a stay or a detour.\n'
            'Policy: Retrieve the conditions on notifying a private extension, comparison fares, reimbursement of necessary business costs and any length-dependent exceptions.\n'
            'Compare: Identify the business dates and private dates, the business-only comparison itinerary, and who bears each added fare or night. A long private extension alone does not prove an overclaim when the university pays only the eligible business portion.\n'
            'Out of scope: Trip approval timing, ordinary invoice formalities and funding by a third party.\n'
            'Verdict: Not_applicable when no private portion is present. Fail for a demonstrated ineligible private cost charged to the university or an unmet applicable condition. Pass correctly allocated costs; unknown if allocation cannot be established.'
        )
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
            (
            (
            (
            (
            'Subject: A1/E101 social-security documentation for employment-related cross-border travel.\n'
            "Policy: Separate the mandatory application from issuance by the social-security institution and carrying the certificate or permissible substitute during travel. Use each obligation's actual deadline; a recommendation to wait for issuance is not itself a mandatory pre-departure issuance deadline.\n"
            'Compare: Read travel dates, current workflow status and any dated evidence that the employer applied for A1/E101. A dated "beantragt am" field is positive evidence of an initiated application. An unchecked travel-abroad or A1 field in a submitted form establishes only that the field is unmarked, not that the employer never applied through another channel. A missing certificate in a pre-trip packet cannot prove a failure to carry it on a future trip. If the relevant mandatory application is already overdue, identify positive evidence of the missed deadline or an express case record establishing non-application; do not turn packet silence alone into positive proof.\n'
            'Out of scope: Travel authorization, visas, insurance and reimbursement invoices.\n'
            'Verdict: Not_applicable outside the covered employment and destination scope. Pass a documented, timely application if no other binding step already due is violated. Fail only for a demonstrated breach of an obligation already due. Unknown when a material application status remains unverified, including an unmarked field in a pre-trip request without evidence of actual non-application. Cite the decisive case and policy text before failing.'
        )
        )
        )
        )
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
            (
            (
            (
            (
            'Subject: Eligibility and amount of each transport cost for the business part of a trip.\n'
            'Policy: Keep scheduled transport, flights, taxi or hired transfer, rental vehicles and private vehicles separate. A trip between an airport and hotel can use several modes. Apply a mode-specific requirement only when the transport mode is positively identified in the case evidence; the word "transfer", endpoints and price alone do not identify a taxi or hired vehicle. Determine whether a justification or comparator is required at application or only during the later Reisekostenabrechnung.\n'
            'Compare: Read every business transport line as a pre-trip estimate, reservation, incurred fare or submitted claim. For an ambiguous transfer, explicitly state that the mode is unresolved and do not demand a taxi-specific justification at the request stage. If an actual taxi or hire is documented, cite the mode and the exact policy provision for a condition already due. Do not infer a violation from absence of a future claim-stage explanation or comparison in the current packet. For a cost cap, compare a proven claimed amount with the relevant proven cap before failing.\n'
            'Out of scope: Invoice addressee, accommodation, private nights and third-party funding.\n'
            'Verdict: Evaluate every claimed transport line, then combine them: fail for a demonstrated present-stage, mode-specific breach or an incurred claim proven over the applicable cap; pass only if every material transport line has a documented mode and satisfies its present-stage conditions. If any material line names only a generic transfer without identifying whether it is scheduled transport, shuttle, taxi, hired vehicle or another mode, return unknown for the whole transport rule even when flights or rail tickets pass. A later explanation might establish eligibility; the currently unresolved line cannot be certified as pass or treated as a taxi violation. Do not call an ambiguous transfer a taxi.'
        )
        )
        )
        )
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
            (
            (
            (
            'Subject: Formal validity of travel invoices or receipts at the current stage of the case.\n'
            'Policy: Identify the requirements for receipts of incurred travel costs during the later Reisekostenabrechnung, and any separate addressee or invoice formalities already due for an issued invoice. Do not apply a later claim-stage upload requirement to an earlier approval request.\n'
            'Compare: Determine the stage from the application status and trip dates. Inspect each cost line: distinguish a voraussichtliche Kosten (Schätzung) estimate, unpaid reservation, booking confirmation, issued invoice, paid charge and filed expense claim. A future hotel cost in an approval form is not an incurred expense. An invitation or price quote is not a missing receipt, and a booking paid only at checkout cannot be required to have a final receipt before travel. For an invoice already issued, check its actual addressee and any formal defect documented in that invoice. Do not assert the packet is complete or that an unprovided receipt is absent from the eventual reimbursement claim.\n'
            'Out of scope: Whether the transport mode is eligible, hotel rate cap and filing deadline.\n'
            "Verdict: Fail only for a verified defect in a document already due at the shown stage, or a filed expense claim positively shown to lack a required receipt after the expense was incurred. Pass where present-stage invoices meet the requirements; not_applicable where there are only future estimated costs with no invoice due; unknown where a material document's status is unresolved. A pre-trip approval request alone cannot fail for missing future hotel, conference or transfer receipts."
        )
        )
        )
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
            (
            'Subject: Separately claimed social, cultural, accompanying or optional event-program costs.\n'
            'Policy: Identify which conference fees, included meals and optional side-program costs are reimbursable and under what conditions.\n'
            'Compare: Inspect each claimed event line and its description. Distinguish a mandatory professional registration from an optional dinner, excursion or private activity; do not infer a side program solely because a conference is involved.\n'
            'Out of scope: General travel, lodging and the payer of a conference fee.\n'
            'Verdict: Not_applicable without an in-scope event-program line. Fail for a demonstrably ineligible cost claimed; pass compliant lines; unknown when the policy or item description does not settle its category.'
        )
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
            (
            (
            (
            (
            (
            'Subject: Avoiding duplicate university reimbursement when a separate third party benefits the traveler for the same travel costs.\n'
            "Policy: Determine the third party's payer, beneficiary, covered costs, amount, payment status, conditions and the stage when deduction or disclosure is required. A university internal cost centre is not a second payer. A discount on a fee is not a payment of the fee to the traveler.\n"
            "Compare: Separate an offer payable only after travel and original receipts from an irrevocable or already paid benefit. Read the award's actual conditions and specify which payer must reduce which payout. If the outside grantor expressly reduces its later grant for costs paid by the university, the university may pay the requested eligible costs; it is the outside grantor's later payout that must be reduced. Do not invert that direction and say the university must refuse those costs merely because the future grant exists. A full pre-trip university estimate is neither a completed reimbursement nor proof that the grantor skipped a later offset. If the award letter is among the case documents, do not assert nondisclosure to the case reviewer solely because the application form lacks a separate award field; do not assert it reached an external office without evidence either. Determine whether a claim-stage offset or separate notification is already due, rather than importing a future obligation into the current request. Distinguish evidence of a grant's existence from evidence of its payment, and from evidence that its condition was breached. For either pass or fail, quote the document's actual payout timing and its reduction condition, and cite the applicable currently effective policy passage about the treatment of third-party benefits in policy_refs. A budget or project-information passage cannot substitute for that governing provision. Before failing, cite case evidence that establishes an unoffset payment or a currently due disclosure or offset being violated. A quote that explicitly promises future reduction cannot itself prove an unoffset payment.\n"
            'Out of scope: Internal project budgets, transport and accommodation caps, invoice form and mere registration discounts.\n'
            'Verdict: Not_applicable when no separate overlapping benefit is documented. Fail for a proven unoffset overlapping paid benefit or a positively documented violation of a disclosure/deduction already due. Pass an expressly conditional future award whose grantor will reduce its eventual payout for costs paid by the university and whose letter is provided to the current case reviewer, if the policy imposes no other presently due obligation. A pass does not certify that the later grant settlement was completed; say which future deduction remains required. Unknown when a material payment, notification or offset status cannot be established; lack of a separate document is not itself proof of violation. If the available policy passages govern only later Reisekostenerstattung and the case is an earlier request, do not use them as a present-stage prohibition. Return a policy_refs entry for every applicable verdict, including pass; do not return an empty list for a policy-based conclusion.'
        )
        )
        )
        )
        )
        ),
        queries={
            "de": [
                      'Reisekosten Kostenübernahme Dritte Anrechnung',
                      'Leistungen dritter Seite Reisekostenvergütung',
                      'Drittmittelprojekt Dienstreise Zuwendungsgeber',
                      'Dienstreise Kosten von anderer Stelle erstattet',
                      'Drittmittelgeber Bestimmungen Reisekosten Dienstreise',
                      'Dienstreisemanagement Zustimmung Leistungen dritter Seite Reise',
                      'Um die Zustimmung zu erlangen für die Entscheidung maßgeblichen Umstände vollständig vor Antritt der Reise mitzuteilen',
                      'Die erhaltenen Leistungen von dritter Seite werden nach § 4 Abs. 3 HRKG auf die Reisekostenerstattung angerechnet',
                  ],
            "en": [
                "travel costs covered by third party offset",
                "third-party funding travel costs reimbursement",
            ],
        },
        questions={
            "de": [
                      'Wie werden Leistungen von dritter Stelle auf die Reisekostenvergütung angerechnet?',
                      'Welche Bestimmungen gelten für Dienstreisen, die aus Drittmitteln finanziert werden?',
                      'Wann sind Leistungen von dritter Seite vor der Reise mitzuteilen, und wann werden erhaltene Leistungen angerechnet?',
                      'Welche Leistungen von dritter Seite sind für die Zustimmung vor Reiseantritt mitzuteilen?',
                      'Wann werden erhaltene Leistungen von dritter Seite auf die Reisekostenerstattung angerechnet?',
                  ],
            "en": [
                "How are travel costs that are paid by a third party or a funder treated in the reimbursement?",
                "Which rules apply to business trips funded by third-party grants?",
            ],
        },
    ),
]
