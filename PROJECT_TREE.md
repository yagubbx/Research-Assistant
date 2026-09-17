# Yekun layihə ağacı

```text
ResearchAssistant/
├── .github/
│   ├── workflows/
│   │   └── ci.yml
│   └── pull_request_template.md
├── ai/
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── anthropic.py
│   │   ├── base.py
│   │   ├── factory.py
│   │   ├── google.py
│   │   └── openai.py
│   ├── __init__.py
│   ├── schemas.py
│   ├── sources.py
│   └── synthesizer.py
├── artefacts/
│   ├── acceptance.txt
│   ├── ai-integrity.json
│   ├── benchmark.json
│   ├── coverage.json
│   ├── demo.json
│   ├── demo.txt
│   ├── dependency-verification.json
│   ├── docker-acceptance.json
│   ├── docker-verification.txt
│   ├── doctor.json
│   ├── final-verification.json
│   ├── live-benchmark.json
│   ├── live-source-probe.json
│   ├── live-web-probe.json
│   ├── render-live-verification.json
│   ├── tests.xml
│   └── verification.txt
├── data/
│   └── research_questions.json
├── docs/
│   ├── fonts/
│   │   ├── LICENSE
│   │   ├── NotoSans-Bold.ttf
│   │   ├── NotoSans-BoldItalic.ttf
│   │   ├── NotoSans-Italic.ttf
│   │   ├── NotoSans-Regular.ttf
│   │   ├── NotoSerif-Bold.ttf
│   │   ├── NotoSerif-BoldItalic.ttf
│   │   ├── NotoSerif-Italic.ttf
│   │   └── NotoSerif-Regular.ttf
│   ├── BONUSES.md
│   ├── DEFENSE_GUIDE_AZ.md
│   ├── DEPLOY_RENDER.md
│   ├── PROBLEMS_AND_SOLUTIONS.md
│   └── REQUIREMENTS.md
├── presentation/
│   ├── slides.pdf
│   └── slides.tex
├── report/
│   ├── contribution_statement.pdf
│   ├── contribution_statement.tex
│   ├── report.pdf
│   └── report.tex
├── researcher/
│   ├── __init__.py
│   ├── __main__.py
│   ├── bonuses.py
│   ├── cache.py
│   ├── cli.py
│   ├── config.py
│   ├── core.py
│   ├── doctor.py
│   ├── logging_config.py
│   ├── models.py
│   ├── offline.py
│   ├── resilience.py
│   ├── search.py
│   ├── service.py
│   ├── setup.py
│   ├── validation.py
│   ├── web_ui.py
│   └── worker.py
├── scripts/
│   ├── launch.cmd
│   ├── live_benchmark.py
│   └── verify.py
├── tests/
│   ├── conftest.py
│   ├── test_ai_smoke.py
│   ├── test_se_bonuses.py
│   ├── test_se_cache.py
│   ├── test_se_citation_retry.py
│   ├── test_se_cli_service.py
│   ├── test_se_core.py
│   ├── test_se_doctor.py
│   ├── test_se_resilience.py
│   ├── test_se_search.py
│   ├── test_se_setup.py
│   ├── test_se_ui.py
│   └── test_se_validation.py
├── .dockerignore
├── .env.example
├── .gitignore
├── BASLA_AZ.md
├── CHANGELOG.md
├── Dockerfile
├── Dockerfile.render
├── HANDOVER_STATUS.md
├── PROJECT_TREE.md
├── README.md
├── TOPIC.md
├── conftest.py
├── demo_ai.py
├── pyproject.toml
├── pytest.ini
├── render.yaml
├── requirements-dev.txt
├── requirements-providers.txt
├── requirements-ui.txt
├── requirements.txt
├── run_demo.cmd
├── run_ui.cmd
├── setup_gemini.cmd
└── verify_docker.cmd
```

| Qovluq/fayl | Müdafiədə bilməli olduğunuz |
|---|---|
| researcher/*.py | Komandanın izah etməli olduğu tətbiq, keş, concurrency, validation, worker və UI məntiqi |
| ai/*.py, ai/providers/*.py | Müəllimin təqdim etdiyi müqavilə və adapterlər; öz müəllifliyiniz kimi göstərməyin |
| tests/, conftest.py | Nəyin mock edildiyi, uğur/xəta ssenariləri, offline zəmanət |
| artefacts/ | Test, benchmark və qəbul sübutları; hər birinin tarixini və limitini ayırın |
| docs/ | Tələblər, problemlər/həllər, deploy və müdafiə izahları |
| report/, presentation/ | Redaktə edilən .tex və təqdim edilən .pdf; contribution imzaları sizindir |
| requirements*.txt, pyproject.toml, pytest.ini | Asılılıq və keyfiyyət sazlamaları |
| Dockerfile*, render.yaml, .github/ | Konteyner, deploy, CI və PR prosesi |
| *.cmd, scripts/ | Quraşdırma, demo, yoxlama və benchmark köməkçiləri |
| .env.example, .gitignore, .dockerignore | Konfiqurasiya nümunəsi və gizli/generated faylların istisnası |
| docs/fonts/ | PDF üçün lisenziyalı fontlar; sizin yazdığınız kod deyil |

.venv, .git, __pycache__, .pyc, .cache və şəxsi .env təhvil ZIP-inə daxil deyil. Quraşdırılmış cryptography/hazmat kimi kitabxanalar üçün müəlliflik daşımırsınız; hansı dependency-nin niyə istifadə edildiyini izah etməlisiniz.

Signature assets: report/signatures/yaqub.jpeg, sebuhi.jpeg, aqil.jpeg. These accompany the editable contribution_statement.tex.

