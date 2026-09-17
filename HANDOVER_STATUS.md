# Handover checkpoint — 2026-09-17

This source package includes the latest deployment fixes on `deploy/render`.
It supersedes the old v1.1.0 ZIP for source code. The application version remains
1.1.0; use the Git commit to identify this checkpoint precisely.

## Verified deployment

- URL: https://vertex-research-assistant.onrender.com/
- Deployed code checked: `0d6208beb83752f79dc342c5c88d6fd6ca205154`.
- Render model: `gemini-3.1-flash-lite`; local setup and deployment defaults now match.
- Live photosynthesis request: 23.21 seconds, three available sources, three references.
- Sample mode also completed without provider credentials.
- Evidence: `artefacts/render-live-verification.json`.
- Earlier full regression run: 121 passing tests, 93.94% coverage.
  Older artefacts and PDFs retain their original measurement dates/results.

A successful request verifies that flow, not future provider uptime or grading.
No API key, virtual environment or Git history is included in the ZIP.

## Human academic handover remaining

1. Push this branch, then open a pull request from `deploy/render` into `main`.
2. Each teammate reviews and tests their actual area, using their own account.
   Record real contributions; do not manufacture commits or approvals.
3. Update the existing report and slides with these deployment results and the
   final test results. The included PDFs are historical and have not been rebuilt
   for this checkpoint. Complete and sign the contribution statement yourselves.
4. Obtain teammate review and passing CI, then merge the pull request.
5. Change Render to the reviewed `main` branch and deploy that commit; verify
   sample and live flows again after deployment.
6. Tag the reviewed submission `v1.0-final` only after all submission documents
   and signatures are complete. Export the final archive from that tag.

Do not run `git init` again or overwrite the existing repository with a new history.
Use the existing working clone to push. For a separate VS Code workspace, clone
the repository and check out `deploy/render` after it has been pushed.

## Local checks (PowerShell, project root)

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
python -m researcher.setup
python -m researcher doctor
python -m streamlit run researcher/web_ui.py
```

Select Sample demo for offline fixtures; Live research needs internet and a valid
provider key. Keep `.env` private. Never paste a key into GitHub or the report.
