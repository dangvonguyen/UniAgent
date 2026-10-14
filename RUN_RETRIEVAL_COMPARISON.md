# Three-dataset retrieval comparison

`uniagent/benchmark_retrieval.py` runs the retrieval implementation from this
repository on the three datasets used by `../slide/main.tex`:

- `retrieval-de-spot-check`
- `retrieval-en-spot-check`
- `retrieval-hessian-law-de-spot-check`

It reads the existing `uniagent-hybrid/run.txt.gz`,
`weighted-rrf-mq10/run.txt.gz`, and
`weighted-rrf-no-mq/run.txt.gz` files from the original PP04 workspace. It does
not rerun any of them. The no-MQ run remains in the judgment pool so the old
part of the pool, recall denominator, and slide baseline stay unchanged. The
final report compares old UniAgent, new UniAgent, and `weighted-rrf-mq10`.

## Retrieval mapping

Only the new UniAgent run is generated:

- BM25: `query`
- GTE reranking of the top 20 chunks: `query + original_query.description`
- weighted RRF: sparse `0.3`, GTE `0.7`, `k=60`

Passage results are collapsed to their parent `doc_id` with the maximum fused
passage score, matching the slide pipeline's max-chunk-to-parent convention.

## Evaluation

The script imports the original evaluator from
`../tools/pooled_retrieval_eval/src` and performs the complete judgment flow:

1. Stage the old UniAgent run and the two runs from the slide's final pool.
2. Generate only the new `uniagent-bm25-gte` run.
3. Form one blind shared top-30 pool from all four runs.
4. Reuse labels from the final pipeline qrels by default.
5. Send only query-document pairs absent from those seed qrels to UMBRELA.
6. Parse and persist every label with parser v2 (`2.0`).
7. Evaluate the three requested runs against the resulting shared qrels.

It reports:

- graded nDCG@10, retaining labels 0--3 with linear gain;
- Recall@30 for `rel >= 1` and `rel >= 2`;
- Judged@10 and Judged@30;
- paired bootstrap 95% CI and paired two-sided randomization p-value for
  nDCG@10.

## Run

Two environments are used because the retrieval project targets Python 3.13,
while the organizer-compatible UMBRELA stack is pinned to Python 3.12:

- launch the script from the Python 3.13 environment containing this project's
  retrieval dependencies;
- by default, judging uses `../.venv-umbrela/python.exe` and provider settings
  from `../tools/pooled_retrieval_eval/.env`.

The provider configuration requires `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and
`OPENAI_MODEL`. Values already set in the process environment take precedence
over the `.env` file. The script never writes the API key to its reports.

Run from the clone root:

```powershell
uv sync
uv run python .\uniagent\benchmark_retrieval.py
```

The default expects the old run under the same output root:

```text
runs/three-dataset-retrieval-comparison/<dataset>/runs/uniagent-hybrid/run.txt.gz
```

If it is stored under another completed benchmark root, pass:

```powershell
uv run python .\uniagent\benchmark_retrieval.py `
  --old-runs-root C:\path\to\old-benchmark-output
```

If `uv` is not installed yet:

```powershell
python -m pip install uv
uv sync
uv run python .\uniagent\benchmark_retrieval.py
```

To inspect how many new judgments are required without calling the provider:

```powershell
python .\uniagent\benchmark_retrieval.py --prepare-only
```

The broader 9,159-pair canonical qrels from slide 3 can be used as the seed
instead of the final pipeline qrels. UMBRELA still judges every pooled pair
absent from that seed:

```powershell
python .\uniagent\benchmark_retrieval.py --seed-qrels-source canonical
```

The default paths are derived from this layout:

```text
PP04/
|-- data/
|-- outputs/
|-- tools/
|-- slide/
`-- PP04-task2/       <- this repository
```

To use explicit paths:

```powershell
python .\uniagent\benchmark_retrieval.py `
  --workspace-root C:\coding_space\paper\PP04 `
  --output C:\coding_space\paper\PP04\PP04-task2\runs\three-dataset-retrieval-comparison `
  --umbrela-python C:\coding_space\paper\PP04\.venv-umbrela\python.exe `
  --env-file C:\coding_space\paper\PP04\tools\pooled_retrieval_eval\.env
```

The main outputs are:

```text
runs/three-dataset-retrieval-comparison/
|-- <dataset>/runs/uniagent-hybrid/run.txt.gz
|-- <dataset>/runs/uniagent-bm25-gte/run.txt.gz
|-- <dataset>/runs/weighted-rrf-mq10/run.txt.gz
|-- <dataset>/runs/weighted-rrf-no-mq/run.txt.gz
|-- <dataset>/pooled-judgments/pools/top-30-pool.json
|-- <dataset>/pooled-judgments/requests/<qid>.json
|-- <dataset>/pooled-judgments/responses/<qid>.json
|-- <dataset>/pooled-judgments/qrels.txt
|-- <dataset>/comparison/{summary,per-query,pairwise}.csv
|-- <dataset>/comparison/report.{md,json}
|-- reports/cross-dataset/report.{md,json}
`-- manifest.json
```

After the retrieval run exists, the workflow can resume without indexing or
embedding inference. Persisted UMBRELA responses are validated and reused, so
completed pairs are not sent to the provider again:

```powershell
python .\uniagent\benchmark_retrieval.py --evaluation-only
```

The workflow audits every persisted response and rejects the result unless its
judgment provenance records parser version `2.0`. With the default top-30 pool,
Judged@30 should therefore be `1.0` for all three reported runs.
