from src.quotes import match_case_quote, match_policy_quote

POLICY = (
    "Travel expenses - INTERNAL\n\n"
    "Taxi rides\n\n"
    "Taxi costs over 30 € are only reimbursed with a written justification. "
    "Without a justification, no reimbursement is possible.\n\n"
    "Contact"
)

INVOICE = (
    " Description         Qty       VAT       gross\n"
    " Coffee, 1 kg            3      7%      40.47 €\n"
    " Total                                  40.47 €"
)


def test_policy_exact_quote_returns_source_text():
    quote = "Taxi costs over 30 €  are only\nreimbursed with a written justification."
    assert match_policy_quote(quote, POLICY, "en") == (
        "Taxi costs over 30 € are only reimbursed with a written justification."
    )


def test_policy_fuzzy_drops_invented_prefix():
    quote = (
        "Uni Kassel\n\nTaxi costs over 30 € are only reimbursed "
        "with a written justification. Without a justification, no reimbursement "
        "is possible."
    )
    text = match_policy_quote(quote, POLICY, "en")
    assert text is not None
    assert "Uni Kassel" not in text
    assert text.endswith("Without a justification, no reimbursement is possible.")
    assert text in POLICY


def test_policy_misquoted_value_yields_source_value():
    quote = "Taxi costs over 50 € are only reimbursed with a written justification."
    assert "30 €" in match_policy_quote(quote, POLICY, "en")


def test_policy_rejects_unrelated_and_short_quotes():
    unrelated = "Hotel costs are reimbursed at a flat rate per night."
    assert match_policy_quote(unrelated, POLICY, "en") is None
    assert match_policy_quote("over 50 €", POLICY, "en") is None


def test_policy_partial_sentence_widens_to_keep_its_condition():
    policy = "Taxi costs over 30 € are reimbursed, provided a justification is given. Otherwise not."
    text = match_policy_quote("Taxi costs over 30 € are reimbursed", policy, "en")
    assert text == "Taxi costs over 30 € are reimbursed, provided a justification is given."


def test_policy_quote_from_mid_sentence_widens_to_its_start():
    policy = "Preface. For taxi rides over 30 € a justification is required. End."
    text = match_policy_quote("over 30 € a justification is required.", policy, "en")
    assert text == "For taxi rides over 30 € a justification is required."


def test_policy_widening_ignores_abbreviations():
    policy = "Reimbursable are e.g. taxi costs over 30 € with a justification. End."
    text = match_policy_quote("taxi costs over 30 €", policy, "en")
    assert text == "Reimbursable are e.g. taxi costs over 30 € with a justification."


def test_policy_widening_stops_at_line_breaks():
    policy = "Taxi rides\nTaxi costs over 30 € need a justification\nContact"
    text = match_policy_quote("Taxi costs over 30 €", policy, "en")
    assert text == "Taxi costs over 30 € need a justification"


def test_policy_widening_is_capped_for_runaway_sentences():
    long_tail = " and ".join(["another cost type"] * 60)
    policy = f"Taxi costs over 30 € need a justification {long_tail}."
    text = match_policy_quote("Taxi costs over 30 € need", policy, "en")
    assert text == "Taxi costs over 30 € need"


def test_case_accepts_whitespace_and_punctuation_differences():
    assert match_case_quote("Coffee, 1 kg 3 7 % 40.47 €", INVOICE) is not None
    assert match_case_quote("Coffee 1kg  3  7%  40.47", INVOICE) is not None


def test_case_rejects_changed_digits_or_letters():
    assert match_case_quote("Coffee, 1 kg 3 7% 40.74 €", INVOICE) is None
    assert match_case_quote("Cocoa, 1 kg 3 7% 40.47 €", INVOICE) is None


def test_case_quote_is_not_widened():
    assert match_case_quote("Coffee, 1 kg", INVOICE) == "Coffee, 1 kg"


def test_empty_quote_is_rejected():
    assert match_policy_quote("", POLICY, "en") is None
    assert match_case_quote("  ", INVOICE) is None
