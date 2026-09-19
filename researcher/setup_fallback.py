"""Configure optional Serper fallback without printing credentials."""

import getpass
from pathlib import Path

from dotenv import set_key


def main() -> None:
    """Preserve LLM settings while configuring DuckDuckGo followed by Serper."""
    target = Path(__file__).resolve().parent.parent / ".env"
    print("Get a Serper API key from https://serper.dev/ (check your account quota).")
    secret = getpass.getpass("Serper API key (hidden): ").strip()
    if not secret or any(c.isspace() for c in secret):
        raise ValueError("A non-empty API key without whitespace is required.")
    target.touch(exist_ok=True)
    for name, value in {
        "SERPER_API_KEY": secret,
        "WEB_SEARCH_PROVIDER": "duckduckgo",
        "RESEARCH_WEB_FALLBACKS": "serper",
    }.items():
        set_key(str(target), name, value)
    print("Saved locally: duckduckgo -> serper. No live request was performed.")
    print("Restart any running UI. Render requires the same settings in Environment.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, EOFError) as error:
        print(f"Setup failed ({type(error).__name__}). No key is printed.")
        raise SystemExit(2) from None
