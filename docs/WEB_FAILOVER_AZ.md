# DuckDuckGo → Serper ehtiyat axtarışı

Mexanizm hazırdır; aktivləşməsi üçün Serper açarı lazımdır. Gemini açarı ayrıca saxlanılır.

## Lokal quraşdırma

1. https://serper.dev/ saytında öz hesabını yarat və API açarını götür.
2. Layihənin kökündə, aktiv virtual mühitdə işlət:

```powershell
python -m researcher.setup_fallback
```

Açarı gizli girişə yapışdır. Əmr `.env` daxilində yalnız `SERPER_API_KEY`,
`WEB_SEARCH_PROVIDER=duckduckgo` və `RESEARCH_WEB_FALLBACKS=serper` yazır.
Gemini parametrlərini saxlayır. `.env` faylını Git-ə əlavə etmə.

## Render

Service → Environment bölməsində eyni üç dəyişəni yaz, saxla və redeploy et.
Lokal `.env` Render-ə avtomatik ötürülmür. Əvvəldən işləyən lokal UI-ni yenidən başlat.

## Offline keçid testi

```powershell
python -m pytest tests/test_se_fallback_setup.py tests/test_se_bonuses.py -v
```

Test əsas provayderi süni uğursuz edib Serper yoluna keçidi yoxlayır; real internet və açar istifadə etmir.

## Canlı yoxlama

Serper açarı daxil edildikdən sonra ayrıca canlı yoxlama tələb olunur.
Normal sorğu:

```powershell
python -m researcher ask "What is photosynthesis?" --sources web --no-cache
```

Əsas provayder uğurlu olarsa, ehtiyat çağırılmır; bu sorğunun uğuru təkbaşına Serper-i təsdiqləmir.
INFO logunda `web_provider_selected provider=serper` Serper yolunun seçildiyini göstərir.
Fallback-u söndürmək üçün `RESEARCH_WEB_FALLBACKS` dəyərini boşalt.
