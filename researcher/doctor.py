"""Local configuration diagnostics without network requests or secret output."""

import importlib.util
import shutil
import sys

from pydantic import BaseModel, Field

from researcher.config import Settings


class HealthReport(BaseModel):
    """Explain installation/configuration readiness, not provider availability."""

    ready: bool
    mode: str
    python: str
    llm_provider: str
    web_provider: str
    docker_cli_found: bool
    issues: list[str] = Field(default_factory=list)
    note: str = "Local checks only; no provider request or Docker build was performed."


def diagnose(settings: Settings, offline: bool, sources: list[str]) -> HealthReport:
    """Check the current interpreter and only the selected optional adapters."""
    issues = []
    if sys.version_info < (3, 11):
        issues.append("Python 3.11 or newer is required; Python 3.12 is recommended.")
    if not offline:
        try:
            settings.check_credentials(sources)
        except ValueError as error:
            issues.append(str(error))
        module = {"anthropic": "anthropic", "openai": "openai", "gemini": "google.genai"}[
            settings.llm_provider
        ]
        modules = [module]
        if "web" in sources and settings.web_search_provider == "duckduckgo":
            modules.append("duckduckgo_search")
        for name in modules:
            try:
                found = importlib.util.find_spec(name) is not None
            except (ModuleNotFoundError, ValueError):
                found = False
            if not found:
                issues.append(f"Missing {name}; install requirements-providers.txt for live providers.")
    return HealthReport(
        ready=not issues,
        mode="offline" if offline else "live configuration",
        python=sys.version.split()[0],
        llm_provider=settings.llm_provider,
        web_provider=settings.web_search_provider,
        docker_cli_found=shutil.which("docker") is not None,
        issues=issues,
    )


def render_health(report: HealthReport) -> str:
    """Give a concise human-readable installation checklist."""
    lines = [
        f"Configuration: {'OK' if report.ready else 'ACTION REQUIRED'} ({report.mode})",
        f"Python: {report.python}",
        f"LLM: {report.llm_provider}; web: {report.web_provider}",
        f"Docker CLI: {'found' if report.docker_cli_found else 'not found (optional for local Python runs)'}",
        *[f"- {issue}" for issue in report.issues],
        report.note,
    ]
    return "\n".join(lines)
