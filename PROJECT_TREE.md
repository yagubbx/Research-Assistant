# Təhvil faylları — v1.1.0

Bu ağac ZIP-dəki faylları göstərir. `.venv`, quraşdırılmış kitabxanalar və avtomatik keşlər daxil deyil.

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
│   ├── live-benchmark.json
│   ├── live-source-probe.json
│   ├── live-web-probe.json
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
│   ├── test_se_cli_service.py
│   ├── test_se_core.py
│   ├── test_se_doctor.py
│   ├── test_se_resilience.py
│   ├── test_se_setup.py
│   ├── test_se_ui.py
│   └── test_se_validation.py
├── .dockerignore
├── .env.example
├── .gitignore
├── BASLA_AZ.md
├── CHANGELOG.md
├── Dockerfile
├── PROJECT_TREE.md
├── README.md
├── TOPIC.md
├── conftest.py
├── demo_ai.py
├── pyproject.toml
├── pytest.ini
├── requirements-dev.txt
├── requirements-providers.txt
├── requirements-ui.txt
├── requirements.txt
├── run_demo.cmd
├── run_ui.cmd
├── setup_gemini.cmd
└── verify_docker.cmd
```

| Qovluq | Məqsəd |
|---|---|
| `researcher/` | Əsas tətbiq kodu; saxlanmalıdır. |
| `ai/` | Müəllimin verdiyi dəyişdirilməmiş AI modulu; saxlanmalıdır. |
| `tests/` | Offline avtomatik testlər; təhvil üçün saxlanmalıdır. |
| `data/` | Beş orijinal nümunə sual. |
| `artefacts/` | Demo, benchmark və test nəticələri; proqramın işləməsi üçün yox, təhvil sübutu üçün. |
| `docs/` | Tələblər, müdafiə təlimatı və sənəd şriftləri. |
| `report/` | Hesabat və imzalanacaq töhfə bəyanatı; PDF və LaTeX mənbələri. |
| `presentation/` | Təqdimat PDF-i və LaTeX mənbəyi. |
| `scripts/` | Bir əmrlə yoxlama skripti. |
| `.github/` | GitHub CI və review şablonu. |

## Əsas kök faylları

- `requirements.txt`: dörd əsas kitabxana; offline demo üçün kifayətdir.
- `requirements-dev.txt`: əsas kitabxanalar və test/lint/type-check alətləri.
- `requirements-providers.txt`: real AI provider-ləri üçün əlavə SDK-lar.
- `run_demo.cmd`: Windows-da quraşdırma və offline demo.
- `.env.example`: sazlamaların nümunəsi; real açarlar yalnız `.env` faylına yazılır.
- `Dockerfile`: container build; `.dockerignore`: container-dən çıxarılan fayllar.
- `.gitignore`: Git-ə daxil edilməyəcək fayllar.
- `pyproject.toml`, `pytest.ini`: layihə və yoxlama sazlamaları.
- `conftest.py`: testlərdə xarici interneti bloklayan qoruma.
- `demo_ai.py`, `TOPIC.md`: kursdan verilmiş demo və tələblər.
- `README.md`, `BASLA_AZ.md`, `CHANGELOG.md`: istifadə və versiya məlumatı.

## Uzantılar və təmizləmə

`.py` mənbə koddur. `__init__.py` və `__main__.py` normal Python paket fayllarıdır; silinməməlidir. `.pyc` və `__pycache__` avtomatik yaranır, təhvilə daxil edilmir. `.json` və `.xml` məlumat/nəticə, `.md` təlimat, `.tex` sənəd mənbəyi, `.ttf` şriftdir.

`.venv`, `work`, `packages`, `.cache`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.coverage` və `*.log` təhvil ZIP-inə lazım deyil. Aktiv Python mühitinin içindən `cryptography/hazmat` kimi kitabxana hissələrini tək-tək silmək olmaz. Bu kitabxanalar ayrıca mühitdə quraşdırılır, layihənin öz mənbə kodu deyil.


## Yeni faylların müdafiədə rolu

| Fayl | İzah |
|---|---|
| `researcher/bonuses.py` | Web-provider failover və 60 saniyəlik token rezervasiyası |
| `researcher/web_ui.py` | Eyni core-u çağıran Streamlit interfeysi |
| `researcher/setup.py` | Gizli terminal girişi ilə yerli Gemini sazlaması |
| `tests/test_se_bonuses.py`, `test_se_ui.py`, `test_se_setup.py` | Yeni funksiyaların offline sübutları |
| `requirements-ui.txt` | UI və canlı provider asılılıqları |
| `scripts/launch.cmd` | Mövcud Python-u tapır, mühiti qurur, seçilmiş rejimi açır |
| `run_ui.cmd`, `setup_gemini.cmd` | İki kliklə UI və Gemini sazlaması |
| `scripts/live_benchmark.py` | Yalnız istifadəçi işlətdikdə real şəbəkə ölçməsi; pytest-ə daxil deyil |
| `docs/BONUSES.md` | Bonusların məntiqi, testləri və məhdudiyyətləri |

`researcher/` sizin tətbiq qatınızdır: hər üzv məlumat axınını və xətaların idarəsini izah etməlidir. `ai/` müəllimin verdiyi dəyişdirilməmiş moduldur: inteqrasiyasını izah edirsiniz, müəllifliyini özünüzə aid etmirsiniz. Testlər, Docker/CI və sənədlər də təhvilin hissəsidir. Fontlar sənədləri yenidən kompilyasiya etmək üçündür; `cryptography/hazmat` kimi quraşdırılmış üçüncü tərəf kodları ZIP-də yoxdur.
