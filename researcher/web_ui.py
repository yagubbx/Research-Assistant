"""Small Streamlit view using the same typed pipeline as the CLI."""

import asyncio

import streamlit as st

from ai.providers.base import ProviderError
from researcher.cache import JsonCache
from researcher.cli import render
from researcher.config import Settings
from researcher.core import Researcher
from researcher.logging_config import configure_logging
from researcher.offline import questions
from researcher.service import AIService


def main() -> None:
    """Render an explicit sample/live workflow and downloadable evidence."""
    st.set_page_config(page_title="VerteX · Research Assistant", page_icon="📚", layout="wide")
    st.caption("VerteX / RESEARCH WORKSPACE")
    st.title("From a question to cited evidence.")
    st.write("Explore Wikipedia, arXiv and the web in parallel. Inspect the sources behind each answer.")
    with st.sidebar:
        st.header("Research settings")
        mode = st.radio("Mode", ["Sample demo (no API key)", "Live research"])
        offline = mode.startswith("Sample")
        names = st.multiselect("Sources", ["wiki", "arxiv", "web"], default=["wiki", "arxiv", "web"])
        no_cache = st.checkbox("Fetch again (bypass cache)", value=False)
        st.divider()
        st.caption("Yaqub Xəlilli · Səbuhi Xamiyev · Aqil Əsgərov")
    if offline:
        st.info("Sample mode uses synthetic educational evidence. It does not search the internet.")
        question = st.selectbox("Choose a research question", questions())
    else:
        st.info("Live mode uses the provider and API key in your local .env. Run python -m researcher.setup first.")
        question = st.text_area("Your research question", placeholder="What is photosynthesis?")
    signature = (mode, question, tuple(names), no_cache)
    if st.session_state.get("selection") != signature:
        st.session_state.pop("result", None)
        st.session_state["selection"] = signature
    if st.button("Research", type="primary", disabled=not names):
        try:
            settings = Settings.from_env()
            configure_logging(settings.log_level)
            if offline:
                settings = settings.model_copy(update={"rate_interval": 0, "arxiv_interval": 0})
            key = (offline, settings.model_dump_json())
            if st.session_state.get("pipeline_key") != key:
                if "runner" in st.session_state:
                    st.session_state.runner.close()
                st.session_state.runner = asyncio.Runner()
                namespace = "offline-v1" if offline else (
                    f"live-v1-{settings.web_search_provider}-{settings.web_fallbacks}-{settings.max_results}"
                )
                st.session_state.pipeline = Researcher(
                    settings, JsonCache(settings.cache_dir, settings.cache_ttl, namespace),
                    AIService(settings, offline),
                )
                st.session_state.pipeline_key = key
            with st.spinner("Reading sources and preparing a cited answer…"):
                st.session_state.result = st.session_state.runner.run(
                    st.session_state.pipeline.ask(question, names, no_cache=no_cache)
                )
        except (ValueError, ProviderError, OSError, TimeoutError) as error:
            # Provider/configuration errors may include private upstream content.
            st.error(f"Research could not complete ({type(error).__name__}). Check .env, quota and source selection.")
    if "result" in st.session_state:
        session = st.session_state.result
        columns = st.columns(3)
        columns[0].metric("References", len(session.result.citations))
        columns[1].metric("Elapsed", f"{session.elapsed:.2f}s")
        columns[2].metric("Available sources", sum(bool(s.sources) for s in session.retrieval))
        st.subheader("Answer")
        st.write(session.result.answer)
        st.subheader("References")
        for citation in session.result.citations:
            with st.expander(f"[{citation.index}] {citation.source.title}"):
                st.write(citation.source.snippet)
                st.link_button("Open source", citation.source.url)
        for source in session.retrieval:
            if source.note:
                st.warning(f"{source.name}: {source.note}")
        st.download_button("Download JSON", session.model_dump_json(indent=2), "research.json", "application/json")
        st.download_button("Download answer", render(session), "research.txt", "text/plain")


if __name__ == "__main__":
    main()
