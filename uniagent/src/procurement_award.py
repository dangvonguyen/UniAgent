#!/usr/bin/env python3
"""Audit award selection against stated case criteria and original offers.

The result is factual evidence for a later policy check, never a policy verdict.
No price may be taken from an award table when an original offer is available.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from decimal import Decimal
from pathlib import Path

if __package__:
    from .procurement_consistency import (
        MONEY, _award_money_rows, _id_in_line, money, offer_net, offer_number,
    )
else:  # run as a script from src/
    from procurement_consistency import (
        MONEY, _award_money_rows, _id_in_line, money, offer_net, offer_number,
    )


PRICE_CRITERION = re.compile(
    r"(?i)^\s*Wertung\s+Preis\s*\(netto\)\s*,?\s*"
    r"bei\s+gleicher\s+technischer\s+Eignung\b"
)
EQUIVALENCE = re.compile(
    r"(?i)\b(?:all\w*|beid\w*)\b[^\n.]{0,100}"
    r"\b(?:erfüllen|gleichwertig)\b"
)


def source(document: str, quote: str) -> dict[str, str]:
    return {"document": document, "quote": quote.strip()}


def audit_texts(case_id: str, documents: dict[str, str]) -> dict:
    note = documents.get("vergabevermerk.pdf", "")
    report = {"case_id": case_id, "rule_id": "award_selection",
              "assessment": "needs_review", "selected_net": None,
              "lowest_equivalent_net": None, "difference_net": None,
              "selected_offer_id": None, "offers_compared": 0,
              "evidence": [], "note_price_conflicts": [], "coverage_gaps": [],
              "policy_verdict": None}
    gaps = report["coverage_gaps"]
    if not note.strip():
        report["assessment"] = "no_award_note"
        return report

    criterion = next((line for line in note.splitlines()
                      if PRICE_CRITERION.search(line)), None)
    equivalence = next((line for line in note.splitlines()
                        if EQUIVALENCE.search(line)), None)
    if not criterion:
        gaps.append("No explicit net-price criterion with equal technical suitability")
    if not equivalence:
        gaps.append("Award note does not establish equal suitability of all offers")

    request = documents.get("beschaffungsantrag.pdf", "")
    vendor_lines = [line for line in request.splitlines()
                    if re.match(r"(?i)^\s*Vorgesehener\s+Lieferant\b", line)]
    award_lines = [line for line in note.splitlines()
                   if re.match(r"(?i)^\s*Zuschlag\s+an\b", line)
                   and MONEY.search(line)]
    if len(vendor_lines) != 1 or len(award_lines) != 1:
        gaps.append("Selected offer not uniquely established by request and award note")
    offers = []
    for name, body in sorted(documents.items()):
        if not re.fullmatch(r"angebot-.*\.pdf", name, re.I):
            continue
        identity, net = offer_number(body), offer_net(body)
        if not identity or net is None:
            gaps.append(f"{name}: original offer ID or net total unreadable")
            continue
        rows = _award_money_rows(note, identity)
        if len(rows) != 1:
            gaps.append(f"{name}: offer ID has {len(rows)} matching price rows in award note")
            continue
        original, amount_line = net
        noted = money(rows[0])
        if original != noted:
            report["note_price_conflicts"].append({
                "offer_id": identity, "original_net": str(original),
                "recorded_net": str(noted),
                "sources": [source(name, amount_line),
                            source("vergabevermerk.pdf", rows[0])],
            })
        offers.append((identity, original, name, amount_line, rows[0]))
    report["offers_compared"] = len(offers)
    priced_table_rows = [line for line in note.splitlines()
                         if len(MONEY.findall(line)) >= 2
                         and re.search(r"\s+[1-9]\d*\s*$", line)]
    if len(priced_table_rows) != len(offers):
        gaps.append("Award table and linked original offers have different counts")
    if len(offers) < 2:
        gaps.append("Fewer than two linked, priced original offers")

    selected = []
    if len(vendor_lines) == 1:
        selected = [offer for offer in offers if _id_in_line(offer[0], vendor_lines[0])]
        if len(selected) != 1:
            gaps.append("Request does not uniquely link the selected original offer ID")
    if len(selected) == 1 and len(award_lines) == 1:
        identity, selected_net, name, amount_line, note_row = selected[0]
        report["selected_offer_id"] = identity
        report["selected_net"] = str(selected_net)
        if money(award_lines[0]) != selected_net:
            gaps.append("Award decision amount differs from selected original offer")
        if money(note_row) != selected_net:
            gaps.append("Award table amount differs from selected original offer")

    if gaps:
        return report
    cheapest = min(offers, key=lambda item: item[1])
    report["lowest_equivalent_net"] = str(cheapest[1])
    report["difference_net"] = str(selected[0][1] - cheapest[1])
    report["evidence"] = [
        source("vergabevermerk.pdf", criterion),
        source("vergabevermerk.pdf", equivalence),
        source("beschaffungsantrag.pdf", vendor_lines[0]),
        source("vergabevermerk.pdf", award_lines[0]),
        source(selected[0][2], selected[0][3]),
        source(cheapest[2], cheapest[3]),
    ]
    report["assessment"] = (
        "selection_contradicts_stated_criterion"
        if selected[0][1] > cheapest[1] else "consistent_with_stated_criterion"
    )
    return report


def update_master(master: Path, run_name: str, results: list[dict]):
    master.parent.mkdir(parents=True, exist_ok=True)
    current = master.read_text(encoding="utf-8") if master.exists() else "# Procurement runs\n"
    marker = "<!-- RULE5_RUNS_END -->"
    if marker not in current:
        current = current.rstrip() + "\n\n## Rule 5: award selection (offline)\n\n" \
            "| Lượt | Contradiction | Consistent | Review | No note |\n" \
            "| --- | ---: | ---: | ---: | ---: |\n" + marker + "\n"
    if run_name not in current:
        count = lambda status: sum(row["assessment"] == status for row in results)
        row = f"| [{run_name}]({run_name}/selection-audit.json) | " \
              f"{count('selection_contradicts_stated_criterion')} | " \
              f"{count('consistent_with_stated_criterion')} | " \
              f"{count('needs_review')} | {count('no_award_note')} |\n"
        current = current.replace(marker, row + marker)
    master.write_text(current, encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--master-readme", type=Path)
    args = p.parse_args()
    cases = sorted(path for path in args.input.glob("beschaffungsantrag-*") if path.is_dir())
    if not cases:
        p.error("No procurement cases found")
    results = []
    for case in cases:
        documents = {pdf.name: subprocess.run(
            ["pdftotext", "-layout", str(pdf), "-"], capture_output=True,
            text=True, check=True).stdout for pdf in sorted(case.glob("*.pdf"))}
        results.append(audit_texts(case.name, documents))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    for row in results:
        print(f"{row['case_id']}: {row['assessment']}; selected={row['selected_net']}; "
              f"lowest={row['lowest_equivalent_net']}; "
              f"gap={len(row['coverage_gaps'])}; note_conflicts={len(row['note_price_conflicts'])}")
    print(f"Report: {args.output}")
    if args.master_readme:
        update_master(args.master_readme, args.output.parent.name, results)
        print(f"Main README: {args.master_readme}")


if __name__ == "__main__":
    main()
