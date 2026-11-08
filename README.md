# UniAgent: Rule-Based Case Decision Agent

Our system for the **solving** sub-task of the [UniAgent shared task @ CIKM 2026](https://uniagent.webis.de/cikm26/uniagent26-web/index.html).

The agent decides administrative cases at a German university. It labels each case *angenommen* (accepted) or *abgelehnt* (rejected). It does not ask an LLM for one overall verdict. Instead, it checks each case against a fixed set of rules. Retrieval over the background corpora finds the parameters for each rule, such as limits, deadlines and required documents. A case is rejected if any rule fails.

One `predict.py` handles all three task areas. The prefix of each case directory's name selects the rule set:

| Directory prefix | Task | Rules |
|---|---|---|
| `dienstreiseantrag-XX` | business-trip approval | `src/rules/business_trip.py` |
| `auslagenerstattung-XX` | reimbursement of privately advanced costs | `src/rules/expense_reimbursement.py` |
| `beschaffungsantrag-XX` | internal procurement | `src/rules/procurement.py` |

## Pipeline

`predict.py` runs in three phases:

1. **Index the corpora.** Every corpus under `inputs/retrieval-corpora/` is split into passages and indexed twice: BM25 (PyTerrier, with a stemmer and stopwords for the corpus language) and dense (`static-similarity-mrl-multilingual-v1`). The two rankings are merged with reciprocal rank fusion. The passages, indices and embeddings are cached in `runs/`.
2. **Build the policy digest.** For every rule of the domains in the input, the agent retrieves policy passages and has the LLM pick the text the rule depends on. This happens once per run, and every case reuses the result. Each policy quote is checked against its source text, so the agent can't cite text that isn't there.
3. **Decide each case.** The agent reads the case PDFs and extracts the case facts once. Each rule is then checked against those facts and the rule's policy text. Every check returns `pass` or `fail`, with quotes from the case and from the policy. Procurement cases also get deterministic audits, such as amount and consistency checks. Cases run concurrently.

## Repository layout

```
uniagent/
├── predict.py          # entry point
├── run.sh              # example local run
├── Dockerfile          # TIRA submission image
├── src/
│   ├── retrieval/      # passages, BM25 + dense indices, fusion
│   ├── rules/          # rule definitions per domain
│   ├── digest.py       # resolve rules against the corpora
│   ├── facts.py        # case fact extraction
│   ├── check.py        # per-rule case checks
│   ├── quotes.py       # quote verification
│   ├── business/       # business-trip evidence
│   ├── reimbursement/  # reimbursement checks
│   └── procurement/    # procurement audits
├── eval/               # retrieval evaluation against gold.json
└── tests/
```

## Configuration

Set an OpenAI-compatible endpoint:

```bash
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=dummy
export OPENAI_MODEL=openai/gpt-oss-20b
```

The tunable constants are in `uniagent/src/config.py`. They include retrieval depth, RRF `k`, passage size and LLM sampling.

## Run locally

This needs Python 3.13+, Java 21 and `poppler-utils`.

```bash
uv sync
cd uniagent
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
python3 predict.py \
  --input ../data/datasets/business-trip-dev/inputs \
  --output ./runs \
  --max-tokens 4000
```

To run only some rules, pass their IDs, for example `--rules trip_approval transport_costs`.

## Run with Docker

```bash
cd uniagent
docker build --tag uniagent .
docker run --rm \
  --env OPENAI_BASE_URL \
  --env OPENAI_API_KEY \
  --env OPENAI_MODEL \
  --volume "$PWD/../data/datasets/business-trip-dev/inputs:/input:ro" \
  --volume "$PWD/output:/output" \
  uniagent \
  --input /input \
  --output /output
```

The image bakes in the embedding model and the Terrier jars, so it runs with no internet access.

## Output

- `predictions.jsonl`: one line per case, `{"antrag": "<case-id>", "result": "angenommen" | "abgelehnt"}`
- `run-trace.jsonl.log.gz`: an event trace for every retrieval, model call and decision, including the reasons for each rule verdict and the quotes behind it
