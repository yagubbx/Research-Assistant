# Bonus implementation and evidence — v1.1.0

The course caps bonuses at +10 and decides the award. This file does not claim an awarded score.

| Feature | Implementation | Evidence | Remaining acceptance |
|---|---|---|---|
| Web-provider failover (+3 candidate) | `FailoverProvider`, `AIService._fetch_web_provider`, isolated worker | Offline chaos tests: failed primary, timeout, empty result, secondary success, exhausted providers, cancellation; service integration test | Live two-provider run needs valid configured provider access |
| Token-aware limiter (+2 candidate) | `TokenBudget`; reservation before each live synthesis attempt | Virtual-time test: 7/10 tokens reserved; next request for 4 sleeps 60 seconds. Oversized and concurrent reservation tests | Set TPM to the selected account/model's actual quota |
| Streamlit UI (+2 candidate) | `researcher/web_ui.py`, same `Researcher` pipeline as CLI | AppTest full offline workflow + missing credentials + empty selection; browser demo inspected | Container UI health passed; live LLM workflow still needs a key |
| CI (+2 candidate) | `.github/workflows/ci.yml`: lint, mypy, offline tests, coverage, Docker CLI/UI checks | Local component checks pass | Push workflow, obtain green hosted run, require `quality` in protected main |

## Configuration and trade-offs

Default simple setup: Gemini plus DuckDuckGo. Only a Gemini key is needed. This has ONE web provider, so it does not pretend to demonstrate live multi-provider failover.

For real failover, use Tavily as primary (structured research search) and DuckDuckGo as the keyless secondary:

```env
WEB_SEARCH_PROVIDER=tavily
TAVILY_API_KEY=your-local-key
RESEARCH_WEB_FALLBACKS=duckduckgo
RESEARCH_WEB_PROVIDER_TIMEOUT=6
RESEARCH_SOURCE_TIMEOUT=20
```

Each adapter gets a separate deadline and retry budget. Environment selection is isolated inside a child process; simultaneous sessions cannot change each other's provider. The course `ai/` files remain unchanged. A fallback can have different coverage and ranking. Logs identify the selected web provider. An empty primary also triggers fallback. No result from Wikipedia is disguised as a web result.

`TokenBudget` uses a 60-second sliding window and an asyncio lock. UTF-8 prompt/evidence bytes plus 3072 tokens of formatting/output allowance are reserved before dispatch, including each retry. This is a conservative **estimate**, not a tokenizer or provider-reported billing count. Failed attempts retain reservations. The overall synthesis deadline includes budget waiting. Oversized reservations fail immediately rather than waiting forever.

`RESEARCH_GEMINI_TPM`, `RESEARCH_OPENAI_TPM`, and `RESEARCH_ANTHROPIC_TPM` each default to 60000 as application settings, not asserted provider quotas. Set the selected value using AI Studio/provider account limits. The budget persists across the CLI's demo requests or a UI session; it is not shared across separate processes, machines or other applications using the same API key. It cannot guarantee the account never receives 429.

The UI retains its pipeline and event loop per session, so repeated clicks reuse pacing and token history. It exposes sample/live modes, source selection, cache bypass, references, missing-source notes and JSON/text downloads. No UI code calls a provider directly. API keys stay in `.env` and are not entered into browser widgets.

## Commands

```bash
python -m pytest tests/test_se_bonuses.py tests/test_se_ui.py -v
python -m streamlit run researcher/web_ui.py --global.developmentMode false
docker build -t vertex-research .
docker run --rm -p 127.0.0.1:8501:8501 --entrypoint python vertex-research -m streamlit run researcher/web_ui.py --global.developmentMode false --server.address 0.0.0.0 --browser.gatherUsageStats false
```

The multi-stage image includes UI dependencies. Build, offline CLI, doctor and container UI HTTP health passed (saved host log). Image size:338,510,564 bytes; no <=250 MB image-size bonus is claimed.
