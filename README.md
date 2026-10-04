# UniAgent CIKM26

Agent for [UniAgent 2026](https://uniagent.webis.de/cikm26/uniagent26-web/index.html) Task 2 (Solving): it reviews business-trip, procurement and expense-reimbursement applications and decides `angenommen` / `abgelehnt`. Submissions run in [TIRA](https://www.tira.io/task-overview/uniagent-2026/) (task `uniagent-2026`).

## Local run

The LLM endpoint is configured through `OPENAI_BASE_URL`, `OPENAI_API_KEY` and `OPENAI_MODEL`. For local testing, put them in `uniagent/.env` (git-ignored, never committed):

```bash
cd uniagent
cp .env.example .env   # then fill in the endpoint and key
sh run.sh
```

`run.sh` reads `.env` and writes `predictions.jsonl` and `run-trace.jsonl.log.gz` to `./runs`.

## Docker

```bash
cd uniagent
docker build -t uniagent .
docker run --rm --env-file .env \
  -v "$PWD/../data/datasets/business-trip-spot-check/inputs:/input:ro" \
  -v "$PWD/runs:/output" \
  uniagent --input /input --output /output
```

The TIRA sandbox has no network access. The Terrier jars are therefore downloaded at image build time and PyTerrier runs in offline mode (`PYTERRIER_OFFLINE=1`).

### Docker Desktop setup (Windows / macOS)

Before submitting to TIRA:

1. **Turn off containerd image store:** Docker Desktop → Settings → General → untick **"Use containerd for pulling and storing images"** → Apply & restart. Otherwise images are pushed in OCI format and TIRA rejects them with *"The uploaded image is incompatible with the cluster"* ([details](https://www.tira.io/t/ensure-to-upload-compatible-docker-images)).
2. **Keep LF line endings (Windows):** with `core.autocrlf=true`, `predict.py` is checked out with CRLF and its shebang becomes `python3\r`, so the container fails to start. Disable it for this repo and re-checkout:

   ```bash
   git config core.autocrlf false
   git rm -r --cached -q . && git reset --hard
   ```

## TIRA submission

```bash
pip install tira                     # or: uv tool install tira
tira-cli login --token <TEAM_TOKEN>  # token from the TIRA "Submit" page
tira-cli verify-installation --task uniagent-2026 --team <TEAM>
```

On Windows, set `PYTHONUTF8=1` first, otherwise `tira-cli` crashes when printing status symbols.

The git working tree must be clean. Then, from `uniagent/`, load the LLM settings for the local pre-upload test and submit:

```bash
set -a; . ./.env; set +a
tira-cli code-submission --path . --task uniagent-2026 \
  --dataset business-trip-spot-check-20260907-training \
  --command '/app/predict.py --input $inputDataset --output $outputDir' \
  --forward-environment-variable OPENAI_BASE_URL OPENAI_API_KEY OPENAI_MODEL \
  --allow-network
```

Add `--dry-run` to only build and test locally. `--allow-network` and the forwarded variables are used only for the local test run; inside TIRA the hosted LLM is provided by the environment. The variables are forwarded, not stored in the image.

After the upload, open the task page in TIRA → **Submit** → **Code Submission**, select the uploaded software, then choose a dataset and click **RUN**. Spot-check datasets:

- `business-trip-spot-check-20260907-training`
- `task-2-procurement-spot-check-20260928-training`
- `task-2-expense-reimbursement-spot-check-20260928-training`
