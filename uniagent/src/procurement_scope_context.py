"""Retain adjacent product scope and order duty from retrieved policy passages.

This runs after digest cache loading. It adds only exact, contiguous source spans
from the same document; it does not infer that an unlisted item is covered.
"""
from __future__ import annotations

import re


def adjacent_clauses(text: str) -> list[str]:
    paragraphs = text.split("\n\n")
    found: list[str] = []
    for scope, duty in zip(paragraphs, paragraphs[1:]):
        # Require a short paragraph assigning a contract to a *product class*.
        # A long page about accounting categories and framework partners is
        # not itself evidence that those categories have framework contracts.
        if not (len(scope) <= 500
                and re.search(r"(?iu)\brahmenvertr[aä]g\w*\b|\brahmenvereinbarung\w*\b", scope)
                and re.search(r"(?iu)\b(?:lieferung|beschaffung)\s+von\b", scope)
                and not re.search(r"(?iu)\b(?:kein|keinen|keine|keinem)\b.{0,45}\brahmenvertrag", scope)):
            continue
        if not (len(duty) <= 300
                and re.match(r"(?iu)^\s*(?:die|diese)\s+bestell\w*\b", duty)
                and re.search(r"(?iu)\b(?:muss|müssen|ausschließlich|"
                              r"sind\b[^.]{0,80}\bzu\b)\b", duty)):
            continue
        quote = scope + "\n\n" + duty
        if len(quote) <= 1200 and quote in text and quote not in found:
            found.append(quote)
    return found


async def retain_retrieved_scope(resolved_rules, index, trace) -> None:
    """Attach verified scope+duty pairs from the framework rule's top hits."""
    from .config import DIGEST_CONTEXT_K, RETRIEVAL_DEPTH
    from .models import PolicyQuote

    framework = next((r for r in resolved_rules
                      if r.rule.id == "framework_contract_sourcing"), None)
    if framework is None:
        return
    hits = await index.search(framework.rule.queries, framework.rule.questions,
                              depth=RETRIEVAL_DEPTH)
    seen = {(q.corpus, q.doc_id, q.quote) for q in framework.quotes}
    added = []
    for hit in hits[:DIGEST_CONTEXT_K]:
        passage = hit.passage
        # Top-ranked hits can land two passages *after* the product contract.
        # Inspect a bounded predecessor window in the same indexed document.
        passages = [passage]
        cursor = passage
        for _ in range(3):
            previous = index.previous_passage(cursor)
            if previous is None or previous.corpus != passage.corpus or previous.doc_id != passage.doc_id:
                break
            passages.append(previous)
            cursor = previous
        source_pairs = [(p.text, (p,)) for p in passages]
        for earlier, later in zip(passages[1:], passages[:-1]):
            if later.start_char - earlier.end_char == 2:
                source_pairs.append((earlier.text.rsplit("\n\n", 1)[-1]
                                     + "\n\n" + later.text.split("\n\n", 1)[0],
                                     (earlier, later)))
        for source_text, carriers in source_pairs:
            for clause in adjacent_clauses(source_text):
                for carrier in carriers:
                    key = (carrier.corpus, carrier.doc_id, carrier.text)
                    if key in seen:
                        continue
                    seen.add(key)
                    item = PolicyQuote(corpus=carrier.corpus, doc_id=carrier.doc_id,
                                       quote=carrier.text, title=carrier.title)
                    framework.quotes.append(item)
                    added.append({"corpus": item.corpus, "doc_id": item.doc_id,
                                  "passage_id": carrier.passage_id,
                                  "quote": carrier.text, "title": carrier.title})
    trace.log("observation", tool="retrieved_scope_context",
              output={"rule_id": framework.rule.id, "added": added,
                      "searched_hits": min(len(hits), DIGEST_CONTEXT_K)})
    # A framework call-off is an explicit exception to the comparison-offer
    # default. Reuse only the exact scope+duty spans verified against the
    # retrieved source, so the offers rule can assess that exception per item.
    # Do not assert that every other item is exempt or that no other contract
    # exists outside the retrieved packet.
    offers = next((r for r in resolved_rules if r.rule.id == "comparison_offers"), None)
    shared = []
    if offers is not None:
        offer_keys = {(q.corpus, q.doc_id, q.quote) for q in offers.quotes}
        for source in added:
            key = (source["corpus"], source["doc_id"], source["quote"])
            if key in offer_keys:
                continue
            offer_keys.add(key)
            offers.quotes.append(PolicyQuote(corpus=key[0], doc_id=key[1], quote=key[2], title=source["title"]))
            shared.append({"corpus": key[0], "doc_id": key[1],
                           "passage_id": source["passage_id"]})
    trace.log("observation", tool="framework_scope_for_comparison_offers",
              output={"rule_id": "comparison_offers", "shared": shared,
                      "note": "Scope evidence only; obligations and exceptions require item-level assessment."})
