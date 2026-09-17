# VerteX — Async Research Assistant

Topic 4 of the AI Academy Software Engineering final project. Ask a question, retrieve Wikipedia, arXiv and web-search evidence concurrently, and receive a concise answer with numeric references.

**Team:** Yaqub Xəlilli (`yagubbx`), Səbuhi Xamiyev (`KhamiyevSebuhi`), Aqil Əsgərov (`agilasgarli-sys`).

**Repository:** [yagubbx/Research-Assistant](https://github.com/yagubbx/Research-Assistant).

## launch the presentation UI

1. Extract the complete ZIP into a writable folder.
2. Double-click **run_ui.cmd**. The launcher finds Python, creates a local `.venv`, installs pinned dependencies once and opens Streamlit.
3. Choose **Sample demo (no API key)**, select a question, click **Research**.

For real research, create a Gemini Free Tier key in [Google AI Studio](https://aistudio.google.com/apikey), run **setup_gemini.cmd**, paste the key into its hidden terminal prompt, then select **Live research** in the UI. No paid plan is enabled by the app. Model availability and quota depend on your Google account. `.env` is private and excluded from the ZIP/Git.

Python 3.12 is recommended. The launcher tries the Windows Python launcher, Python on PATH, then an existing Codex Python runtime when available on this machine. On another computer install Python if none is found. First installation needs internet; subsequent sample demos use the installed local environment. `run_demo.cmd` runs all five samples in the terminal.

Manual UI command (after installing `requirements-ui.txt`):

```bash
python -m streamlit run researcher/web_ui.py --global.developmentMode false --browser.gatherUsageStats false
```

New features: malformed upstream JSON recovery, ordered web-provider failover, estimated token sliding-window budget, Streamlit UI and hidden-prompt Gemini setup. See `docs/BONUSES.md` for tests, configuration and limitations. These are bonus candidates, not an awarded +9 score.

## Verified status

- **121 tests pass**, including all **16 unchanged course smoke tests**.
- **93.85% application coverage**, with a 60% CI threshold.
- Ruff passes; mypy reports no issues in 18 application files.
- The supplied AI code and starter tests/data/demo match after normalizing line endings; see artefacts/ai-integrity.json.
- All five sample questions run end-to-end in explicitly labeled offline mode.
- Docker build, five-question offline container demo, doctor and container UI HTTP health **passed**; see `artefacts/docker-verification.txt`. Live Gemini research passed on Render (17 September); the supplied PR #1 status showed two successful checks. PR #1 was merged into main at b56bd18. The operator reports Render now deploys main.

## Quick start — Windows

Install Python **3.12** and open a terminal in this folder. No activation or PowerShell execution-policy change is needed:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m researcher demo --offline --no-cache
```

If your Python command is `python` rather than `py`, use `python -m venv .venv`.

## Quick start — macOS / Linux

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m researcher demo --offline --no-cache
```

The following examples assume the virtual environment is activated, or that `python` is replaced with its full environment path.

## Live research

Copy `.env.example` to `.env`. Choose a supported provider/model and fill its key. `LLM_PROVIDER` supports `anthropic`, `openai`, or `gemini`; keys are `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GOOGLE_API_KEY` / `GEMINI_API_KEY`. The supplied providers also support `LLM_API_KEY` as a fallback. Provider-specific model IDs are account-dependent; the example selects Gemini gemini-3.1-flash-lite, matching the verified Render configuration.

Web search supports `tavily`, `serper`, or `duckduckgo`. The first two need `TAVILY_API_KEY` or `SERPER_API_KEY`. DuckDuckGo is keyless, with its own search-library HTTP stack. For full per-HTTP transport visibility, use Tavily or Serper. The keyless adapter runs in a killable worker so its blocking thread cannot defeat the source deadline.

```bash
python -m researcher ask "What is photosynthesis and what are its main stages?"
python -m researcher ask "How do transformers handle long contexts?" --sources wiki,arxiv
python -m researcher ask "How does CRISPR-Cas9 work?" --no-cache --json
python -m researcher demo --no-cache --json --output artefacts/live-demo.json
```

An LLM key is still required when web search is keyless. Never commit `.env`. The CLI reports missing variable names without showing secret values.

## Offline demonstration

```bash
python -m researcher demo --offline --no-cache
python -m researcher ask "photosynthesis" --offline --sources wiki,arxiv
python -m researcher ask "photosynthesis" --offline --json --output artefacts/answer.json
python demo_ai.py --offline --limit 5
```

Offline mode supports the five supplied topics only. Educational snippets are authored fixtures, URLs use `example.org/offline/`, and output explicitly says **SIMULATED**. These are neither scraped sources nor current research claims. Wikipedia and arXiv payloads still pass through the unchanged real parsers; a fake web provider and fake LLM satisfy the supplied interfaces.

Example:

```text
OFFLINE DEMO: synthetic evidence; not live research.
Photosynthesis converts light energy into chemical energy ... [1].
References:
  [1] (wikipedia) SIMULATED: Photosynthesis
      https://example.org/offline/photosynthesis/wikipedia
```

`--sources` accepts a nonempty subset of `wiki,arxiv,web`. `--no-cache` bypasses both reads and writes. `--json` includes citation sources, per-source status, elapsed time and the offline flag. `--output` writes UTF-8. Exit codes: 0 success, 2 validation/provider/I/O failure, 130 interrupted.

## Architecture

```text
CLI -> Researcher -> AIService -> unchanged ai package
          |             |              |
     Cache ABC     retry wrapper   isolated synthesis
      /     \            |
    JSON   memory    shared HTTP client
                      retry transport -> per-host limiter
```

The orchestrator uses `asyncio.gather` with independent deadlines. A failed source becomes a typed outcome and a note under the references. If all sources fail, synthesis is refused. The service isolates synchronous provider work in a subprocess and kills/reaps it on timeout. Pydantic models carry values across boundaries.

The CLI validates citation numbering and requires every answer sentence to contain a valid reference. It also removes dangling markers that the supplied synthesizer leaves in answer text. These are structural checks, not a guarantee that a source logically supports a claim.

## Configuration

All application values are defined in `researcher/config.py` and shown in `.env.example`. Existing shell values override `.env` values.

| Variable | Default | Meaning |
|---|---:|---|
| RESEARCH_SOURCE_TIMEOUT | 20 | Total seconds per source, including queue/retry/pacing |
| RESEARCH_SYNTHESIS_TIMEOUT | 60 | Total synthesis budget; worker killed on expiry |
| RESEARCH_HTTP_TIMEOUT | 8 | HTTP operation timeout |
| RESEARCH_ATTEMPTS | 3 | Maximum retry attempts |
| RESEARCH_BACKOFF | 0.5 | Exponential delay base; 0.5 then 1.0 seconds |
| RESEARCH_CONCURRENCY | 3 | Maximum simultaneous source operations |
| RESEARCH_RATE_INTERVAL | 1 | Seconds between dispatches to a host |
| RESEARCH_ARXIV_INTERVAL | 3 | arXiv host dispatch interval |
| RESEARCH_CACHE_TTL | 3600 | Cached source lifetime in seconds |
| RESEARCH_CACHE_DIR | .cache/researcher | Atomic JSON cache directory |
| RESEARCH_MAX_QUESTION_LENGTH | 2000 | Raw question character limit |
| RESEARCH_MAX_RESULTS | 3 | Per-source result cap |
| RESEARCH_LOG_LEVEL | INFO | DEBUG, INFO, WARNING, ERROR, CRITICAL |

Retries apply to network/unknown provider failures, HTTP 429 and 5xx; permanent 4xx responses are not retried. `Retry-After` supports seconds and HTTP dates. Exhausted transport retries are not multiplied by the outer AI retry. The limiter persists across questions in one app instance; it does not coordinate independent processes.

Cache keys combine namespace, source and normalized question. Normalization ignores case, whitespace and a trailing question mark while preserving meaningful punctuation. Offline and live namespaces never mix. TTL expiry/corruption produces a miss; a disk failure does not destroy a successful answer. Expired records are not automatically evicted from disk.

Diagnostics use JSON logging on stderr, separate from stdout results. Events contain lengths/counts, status and duration. Raw payloads and provider exception strings are deliberately omitted to avoid disclosing credentials or private questions.

## Tests and quality

```bash
python -m pytest tests --cov=researcher --cov-report=term-missing --cov-fail-under=60
python -m ruff check researcher tests/test_se*.py
python -m mypy researcher
```

Results refreshed on 17 September 2026, Python 3.12.14 / Windows: **121 passed; 93.85% coverage**. The coverage denominator is the `researcher` application, not the supplied provider SDK wrappers. Tests cover real offline parsers, cache contracts, 429/503 retries, no 401 retry, Wikipedia summary retries, deadlines, concurrency, worker failures, missing citations and CLI behavior. The root fixture blocks external sockets but allows asyncio's loopback wakeup sockets. No API key is needed.

GitHub Actions performs lint, type checking, coverage, both demos, Docker build and network-disabled Docker execution. Maintainers must set the workflow as a required branch-protection check; a workflow file alone does not configure that policy.

## Parallel-vs-sequential benchmark

```bash
python -m researcher benchmark --offline --repeats 3 --output artefacts/benchmark.json
```

Five questions, three source fetches per question, three repetitions, shared request client, cache reads/writes bypassed. Scheduling order alternates. Each source has 150 ms simulated delay; Wikipedia uses two 75 ms requests. Pacing is disabled only in offline mode. Synthesis is excluded from the benchmark.

| Repetition | Sequential seconds | Parallel seconds |
|---|---:|---:|
| 1 | 2.413 | 0.819 |
| 2 | 2.412 | 0.795 |
| 3 | 2.398 | 0.802 |
| **Median** | **2.412** | **0.802** |

Observed speedup: **3.01×**. No failed or empty outcomes. The slowest source is the remaining retrieval bottleneck; synchronous LLM latency can dominate the full live run. These measurements show simulated I/O overlap, not real provider performance.

To measure live source fetching, omit `--offline`. Inspect `failed_or_empty` before comparing timings; failed retrieval is not an equivalent successful workload. The raw artefact includes machine information and all repetitions.

## Docker

```bash
docker build -t vertex-research .
docker run --rm --network none vertex-research
docker run --rm --env-file .env vertex-research ask "What is photosynthesis?"
docker run --rm -v research-cache:/app/.cache --env-file .env vertex-research demo
```

The image runs as a non-root user. Its default command is the complete offline demo. The host build, offline demo, doctor and container UI health checks passed; the saved log is `artefacts/docker-verification.txt`. The image is 338,510,564 bytes. PR #1 reported two successful checks before merge. Direct dependencies are pinned; the dependency set is not a complete transitive lock.

## Report and defense

- `report/report.pdf`: ten-page report following the supplied template's structure and styling.
- `presentation/slides.pdf`: eleven-frame 16:9 Beamer defense deck, following the supplied template.
- `report/contribution_statement.pdf`: **unsigned** contribution form with real member identities; actual files/PRs/commit shares must be entered before signing.
- Editable `.tex` sources and SIL-licensed Noto fonts are included.
- `docs/DEFENSE_GUIDE_AZ.md`: Azerbaijani walkthrough and ten-minute presentation plan.
- `docs/REQUIREMENTS.md`: complete requirement/evidence matrix and external acceptance steps.

Compile with Tectonic 0.17.0 or XeLaTeX (not pdfLaTeX, because Unicode names use fontspec):

```bash
tectonic report/report.tex
tectonic presentation/slides.tex
tectonic report/contribution_statement.tex
```

Alternatively, run XeLaTeX twice inside each document's directory. Keep `docs/fonts` alongside the report and presentation directories. The fonts are bundled to preserve Azerbaijani characters.

## Release checklist

1. Each member reviews and understands the code; use genuine branches, commits and reviewed PRs.
2. Configure API keys and record a successful live demo; observe hosted CI. Local Docker acceptance is already recorded.
3. Complete and sign the contribution statement using actual work and commit shares.
4. Publish the accepted code to the team repository, protect main and push `v1.0-final`.
5. Submit according to the instructor's current deadline and upload instructions.

The original brief lists May 23, 2026; preparation occurred September 16, 2026. No Moodle submission, backdated work, commit balance or signature is implied.

## Attribution and AI disclosure

The course supplied `ai/`, its smoke tests, sample questions and `demo_ai.py`; they are unchanged. OpenAI Codex substantially drafted the software-engineering layer, tests, Docker/CI configuration and documentation, and performed the recorded local checks. The team provided identities and repository address. Team review and ownership must be documented honestly; no member's work or PR history is manufactured.

The report and slides adapt the course LaTeX templates. Noto fonts retain their included SIL Open Font License. See the report references for Python asyncio, HTTPX transports and pytest documentation used in the design.

## Live benchmark and container UI

The opt-in `python scripts/live_benchmark.py` uses five topical queries against real Wikipedia/arXiv, with the same pacing and cache bypass in both modes. It does not call an LLM or web-search provider. The latest single repetition took 19.656 s sequential and 19.288 s parallel (1.02×), with zero failed/empty outcomes. Network variation and provider pacing dominate; this is not a universal speedup claim. See `artefacts/live-benchmark.json`. The earlier 3.01× result is a separate simulated three-source scheduling experiment.

```bash
docker run --rm -p 127.0.0.1:8501:8501 --entrypoint python vertex-research -m streamlit run researcher/web_ui.py --global.developmentMode false --server.address 0.0.0.0 --browser.gatherUsageStats false
```

Add `--env-file .env` before the image name for live mode. The image now contains UI dependencies and exposes port 8501. Its build/run and container UI health passed. The image is 338,510,564 bytes (about 322.8 MiB); no <=250 MB bonus is claimed. The local browser workflow and automated UI tests also passed. Live Gemini and PR checks passed; main branch protection still requires maintainer confirmation.

## Final handover

Live site: https://vertex-research-assistant.onrender.com/

- [Problems and solutions](docs/PROBLEMS_AND_SOLUTIONS.md)
- [Current verification](artefacts/final-verification.json)
- [Remaining team actions](HANDOVER_STATUS.md)
- [Submission file tree](PROJECT_TREE.md)

Older benchmark and Docker artefacts retain their original measurement context; they are not new measurements of the hosted service.
