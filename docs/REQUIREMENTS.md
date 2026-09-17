# Requirement-to-evidence map — v1.1.0

Scope: Topic 4 plus the common requirements in the supplied brief.
This checklist does not certify institutional submission.

| Requirement | Evidence | State |
|---|---|---|
| Original AI module | `artefacts/ai-integrity.json` | Text-identical after line-ending normalization |
| Original smoke tests | `tests/test_ai_smoke.py` | 16 passing, unchanged |
| Typed settings | `researcher/config.py` | Tested |
| OOP and own abstraction | Cache ABC, two repositories, service, orchestrator, limiter | Implemented |
| Pydantic boundaries | `models.py`, `worker.SynthesisRequest` | Implemented |
| Required ask syntax and sources flag | CLI and source-selection tests | Tested offline |
| Concurrent gather and deadlines | `Researcher.retrieve` | Tested |
| Shared HTTP client | Client-identity assertion in happy-path test | Tested |
| Bounded concurrency | Configurable semaphore and peak-active test | Tested |
| Rate limiting | Per-host spacing across questions; Retry-After | Tested |
| AI and HTTP retries | Decorator and transport, including wiki summaries | Mock HTTP tests |
| Synthesis deadline | Kill and reap worker process | Tested |
| Graceful degradation | Missing-source notes, malformed Wikipedia JSON regression | Tested including invalid title list and summary body |
| TTL cache and no-cache | JSON, canonical keys, read/write bypass | Tested |
| Citations | Numeric references and sentence checks | Structurally tested |
| Validation | Question size, source list, URLs, controls | Tested |
| Logging | Environment-driven JSON stderr events | INFO redacted input/output previews, metadata and timing; full redacted DEBUG payloads |
| Five-question demo | `artefacts/demo.json`, `demo.txt` | Synthetic offline evidence |
| Sequential vs parallel | Three repetitions, three sources, identical workload | Simulated benchmark, about 3.01x |
| Realistic benchmark | `scripts/live_benchmark.py`, `artefacts/live-benchmark.json` | Five topical queries, real Wikipedia/arXiv, one repetition: 19.656s /19.288s; zero failed/empty outcomes. Excludes web and LLM. |
| Offline pytest >=60% | Coverage gate, socket guard, respx | Passed locally on 17 September; see final-verification.json |
| Core module unit tests and errors | `tests/test_se*.py` | Included |
| Local configuration diagnostics | `doctor` command; optional SDK and secret-redaction tests | Tested |
| One-command verification | `scripts/verify.py`, optional Docker checks | Included |
| Type checker and lint | Mypy and Ruff records | Passed locally on 17 September; see final-verification.json |
| Pinned dependencies | Requirements files | Direct dependencies pinned |
| Dockerfile | Multistage, non-root, offline CLI default, UI port8501 | Build, five-question offline CLI and UI health passed; saved host log |
| Docker build/run | `artefacts/docker-verification.txt` | Passed in host Docker; PR 1 checks passed, as shown by team |
| README and env example | Root files | Included |
| Report and slides | Adapted supplied LaTeX/Beamer templates | 10-page report, 11 slides; oral timing needs rehearsal |
| Contribution statement | Team identities and actual-work fields | Unsigned |
| GitHub URL | Team-specified address in documents | Published; PR 1 merged to main at b56bd18 |
| Protected main and reviewed PRs | CI and PR template | Maintainer/team action |
| Balanced real commit history | Must represent actual work | Cannot be generated as evidence |
| Pushed final tag / Moodle | Release checklist | Team action |
| AI assistance disclosure | Report, slides and README | Included |
| Web-provider failover bonus | `bonuses.py`, `service.py`, `worker.py` | Chaos and integration tests; live two-provider run needs configured access |
| Token-aware limiter bonus | `TokenBudget` sliding-window reservations | Estimated tokens, exhaustion/concurrency tests; operator must set actual account TPM |
| Streamlit bonus | `web_ui.py` through same Researcher core | AppTest + browser offline workflow; container UI health passed |
| CI bonus | `.github/workflows/ci.yml` | PR 1 reported two successful checks; main protection requires confirmation |
| Local launch and Gemini setup | `run_ui.cmd`, `run_demo.cmd`, `setup_gemini.cmd` | Sample demo launcher verified in separate venv; hidden-key setup tested with fake key |

Citation validation is structural and rejects uncited sentences, but does not prove that a scientific claim follows from the cited source. The provided 3–6 sentence instruction is in the synthesis prompt, not an enforced sentence-count contract. These limits are disclosed in the report. Bonus candidates are described in `docs/BONUSES.md`; points are assessed by the instructor, not asserted here.

## External acceptance steps

1. A live Render sample passed. Additional live questions can be checked within provider quota; offline five-question demo remains separate.
2. Docker and PR CI checks passed. Require the quality check in branch protection.
3. PR 1 is merged. Review this documentation update, preserve genuine work history and protect main.
4. Complete the contribution statement with actual files, PRs and commit shares, then sign.
5. Push `v1.0-final` after acceptance and submit using the instructor's current instructions.

The supplied brief states May 23, 2026 as the deadline. This package was prepared September 16, 2026; any revised schedule or exception must come from the instructor.
