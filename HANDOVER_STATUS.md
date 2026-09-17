# Yekun təhvil vəziyyəti — 17 sentyabr 2026

## Hazırlanıb

- Son tətbiq kodu: 2ce60bc; PR 1 main-ə b56bd18 ilə birləşdirilib (istifadəçinin GitHub sübutu).
- Render: https://vertex-research-assistant.onrender.com/ ; istifadəçi main deploy-un tamamlandığını bildirib.
- Əvvəlki canlı acceptance: 23.21 saniyə, 3 mənbə, 3 istinad, Gemini gemini-3.1-flash-lite.
- Yenilənmiş README, hesabat, slaydlar, problem-həll sənədi, tələb cədvəli və fayl ağacı.
- Son lokal test/quality nəticələri: artefacts/final-verification.json.

## Komandanın etməli olduğu addımlar

1. Bu sənəd yeniləməsini push edin, PR açın və başqa üzv həqiqi review etsin. CI yaşıl olduqda main-ə merge edin.
2. Hər üzv contribution_statement sənədinə öz real files/PRs/reviews/commit share məlumatını daxil edib imzalasın. Merge müəllifliyi bərabər texniki töhfə deyil.
3. İmzalı PDF-ni ayrıca PR ilə əlavə edin; təsdiqləyib merge edin. API açarını və .env-ni göndərməyin.
4. main protection üçün review və CI tələbini yoxlayın. Aqilin collaborator dəvətinin qəbulunu təsdiqləyin.
5. Hər üç üzv müdafiə məşqi etsin; canlı demo üçün açar/quota, ehtiyat üçün Sample demo yoxlanılsın.
6. Bütün dəyişikliklər main-də olanda v1.0-final tag/release yaradın. Artıq varsa üzərinə yazmayın; əvvəl mövcud tag-ı yoxlayın. Həmin tag-dan yekun ZIP-i çıxarıb müəllimin sisteminə təhvil verin.

İmzalar, fərdi real töhfələr, formal review və rəsmi təhvil agent tərəfindən sizin adınıza təsdiqlənmir.
Paket bu insan addımlarından əvvəlki hazır mənbə/sənəd checkpoint-idir.

## Team contribution account

The coordinator reports approximately 90% joint working sessions, with implementation commits submitted through Yaqub's computer/account. Completed responsibility allocation according to that account: Yaqub — CLI/core/config/models and integration/deploy; Səbuhi — service/worker/resilience/search/bonuses; Aqil — cache/validation/offline/UI and acceptance/document consistency. This is a team-reported allocation, not independently verified sole authorship or proof of individual test execution.

Verified main@fdfcb60: Yaqub 7/9 commits (77.78%), Səbuhi 2/9 (22.22%, both PR #1/#2 merges), Aqil 0/9 (0%). All non-merge commits are under Yaqub's identity. Git counts do not measure labor share. Refresh this snapshot after further merges. See the filled contribution statement; each member must confirm/correct their account and sign personally. AI assistance remains disclosed. The instructor decides whether centralized commits satisfy contribution requirements.

## Signature and diagnostic update
Provided signature images and coordinator-confirmed 18 September 2026 dates are now included in report/. The Git percentages remain explicitly scoped to main@fdfcb60, not the latest history. Doctor now checks ddgs; all 8 doctor tests and targeted Ruff checks pass. Earlier full-suite numbers remain historical.

