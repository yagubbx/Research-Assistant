# Yaqub üçün başlatma təlimatı — v1.1.0

## İndi açarsız işlət

1. ZIP-i tam çıxart. Faylları ZIP pəncərəsinin içindən işə salma.
2. `run_ui.cmd` faylına iki dəfə klik et.
3. İlk dəfə kitabxanaların quraşdırılmasını gözlə; internet lazımdır.
4. Brauzerdə `http://localhost:8501` açılır.
5. **Sample demo (no API key)** rejimində sualı seç, **Research** düyməsini bas.
6. Cavabı, istinadları və mənbə mətnlərini göstər; JSON və mətn kimi yükləyə bilərsən.

Terminalda bütün 5 sualı göstərmək üçün `run_demo.cmd` işlət.
Sample rejimi nümunə məlumatdır, real internet araşdırması kimi təqdim etmə.

## Pulsuz Gemini açarı ilə real araşdırma

1. https://aistudio.google.com/apikey ünvanında Google hesabınla daxil ol və API açarı yarat.
2. Hesabda Free Tier seçiminin və model üçün kvotanın olduğunu yoxla. Ödənişli plana keçmək lazım deyil. Pulsuz istifadə limitsiz deyil.
3. `setup_gemini.cmd` faylını aç. Tövsiyə edilən model: `gemini-2.5-flash`; hesabında mövcud başqa pulsuz modeli də yaza bilərsən.
4. API açarını **gizli terminal sorğusuna** yapışdır və Enter bas. Ekranda görünməməsi normaldır.
5. Açar yalnız yerli `.env`-ə yazılır. Söhbətə və GitHub-a göndərmə.
6. `run_ui.cmd` → **Live research** → sualını yaz → **Research**.

Sazlama Gemini + açarsız DuckDuckGo seçir. Wikipedia/arXiv üçün də açar lazım deyil. Gemini kvotası bitərsə bir müddət gözlə; tətbiq özü ödənişli plan almır.

Əl ilə `.env` yazmaq istəsən:

```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
GOOGLE_API_KEY=oz_acarin
WEB_SEARCH_PROVIDER=duckduckgo
```

Google-un rəsmi məlumatı: https://ai.google.dev/gemini-api/docs/pricing və https://ai.google.dev/gemini-api/docs/api-key . Pulsuz planın əlçatanlığı və limitləri dəyişə bilər.

## Python tapılmırsa

Python 3.12 quraşdır. Başlatma faylı `py`, PATH-dəki Python və bu kompüterdə mövcud əlavə Python runtime-ını avtomatik yoxlayır. `.venv` və kitabxanalar ZIP-ə daxil deyil, ilk açılışda yaradılır. `cryptography/hazmat` kimi kitabxana qovluqları sizin yazdığınız tətbiq kodu deyil; onları mühitin içindən silmə.

## Müdafiə

- `PROJECT_TREE.md`: bütün təhvil faylları və rolları.
- `docs/DEFENSE_GUIDE_AZ.md`: əsas modulların izahı.
- `docs/BONUSES.md`: bonusların məntiqi, testləri və sərhədləri.
- `docs/REQUIREMENTS.md`: tələb–yer–yoxlama cədvəli.
- `report/report.pdf`: yenilənmiş hesabat.
- `presentation/slides.pdf`: yenilənmiş slaydlar.

Yerli demo, testlər, Docker build, konteyner demosu və UI health yoxlaması keçib. Canlı Gemini cavabı üçün şəxsi açar və uyğun kvota lazımdır. GitHub PR/review tarixçəsi və komanda imzaları real komanda işi ilə tamamlanır; onlar avtomatik uydurulmayıb.
