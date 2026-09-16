"""Interactive local Gemini setup: secrets never enter command history."""

import getpass
from pathlib import Path

from dotenv import set_key


def main() -> None:
    """Update only the selected settings; keep unrelated local configuration."""
    target = Path(__file__).resolve().parent.parent / ".env"
    print("Create a Free Tier key: https://aistudio.google.com/apikey")
    print("Choose a model available on your account's free tier. Billing is not enabled by this script.")
    model = input("Model [gemini-2.5-flash]: ").strip() or "gemini-2.5-flash"
    secret = getpass.getpass("Gemini API key (hidden): ").strip()
    if not secret or any(c.isspace() for c in secret):
        raise ValueError("A non-empty API key without whitespace is required.")
    target.touch(exist_ok=True)
    for name, value in {
        "LLM_PROVIDER": "gemini", "LLM_MODEL": model,
        "GOOGLE_API_KEY": secret, "WEB_SEARCH_PROVIDER": "duckduckgo",
    }.items():
        set_key(str(target), name, value)
    print("Saved to local .env. Next: python -m researcher doctor")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, EOFError) as error:
        print(f"Setup failed ({type(error).__name__}). No key is printed.")
        raise SystemExit(2) from None
