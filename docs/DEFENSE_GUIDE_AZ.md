# VerteX — müdafiəyə hazırlıq

AI istifadəsi açıqlamasını saxlayın. Hər üzv proqramı başa düşməli və öz real töhfəsini qeyd etməlidir.

## 10 dəqiqəlik plan

| Vaxt | Mövzu | Təklif olunan danışan |
|---|---|---|
| 0:00–3:00 | Problem, arxitektura, paralellik | Yaqub |
| 3:00–6:30 | Retry, timeout, xəta ssenarisi, CLI demo | Səbuhi |
| 6:30–10:00 | Keş, testlər, Docker, məhdudiyyətlər | Aqil |

Bu bölgü kod müəllifliyini göstərmir; hər kəs tam sorğu axınını öyrənməlidir.

## Sorğunun yolu

1. `cli.main` əmri, `Settings.from_env` konfiqurasiyanı oxuyur.
2. `Researcher.ask` sualı və mənbə siyahısını yoxlayır.
3. `retrieve` bir HTTP client və üç paralel mənbə işi yaradır.
4. Hər iş öz timeout-u daxilində semaphore-dan icazə alır, keşə baxır, lazım olsa AI xidmətini çağırır.
5. HTTP transport alt-sorğulara da rate limiter və retry tətbiq edir.
6. Uğurlu mənbələr birləşir. Hamısı uğursuzdursa, cavab uydurulmur.
7. Ayrı prosesdə dəyişdirilməmiş `ai.synthesize` çağırılır.
8. `validate_answer` istinad nömrələrini və cümlələrin istinadlarını yoxlayır.
9. CLI cavabı, mənbələri və çatışmayan mənbə qeydlərini göstərir.

## Suallar və qısa cavablar

**Niyə asyncio?** Sorğular internet cavabını gözləyir. Bir iş gözləyəndə digəri irəliləyir; CPU hesablamasını sürətləndirmirik.

**Gather kifayətdirmi?** Xeyr. Semaphore paralellik həddini, ayrıca timeout isə hər mənbənin vaxt büdcəsini qoruyur.

**Niyə sintez ayrı prosesdədir?** Thread gözləməsini dayandırmaq SDK-nı dayandırmır. Proses öldürülüb bağlana bilir. Pipe gözləməsi thread-də, SDK isə prosesdədir.

**Retry niyə iki qatda var?** HTTP qatı Wikipedia summary kimi alt-sorğuları, AI qatı isə provider xətalarını qoruyur. HTTP cəhdləri tükənəndə xarici retry-nin onları çoxaltmasının qarşısı alınır.

**401 və 429 fərqi?** 401 credential problemidir, eyni sorğunu təkrarlamırıq. 429 rate-limit siqnalıdır, Retry-After əsasında gözləyirik.

**Keş niyə hash istifadə edir?** İstifadəçi sualı fayl adı olmur; hash sabit və təhlükəsiz ad yaradır. Mənbə və offline/live namespace də açara daxildir.

**TTL faylı silirmi?** Xeyr, vaxtı bitmiş məlumat istifadə olunmur. Fiziki disk təmizləməsi ayrıca məsələdir.

**3,01× nəyi göstərir?** Beş sualın süni gecikməli mənbə sorğularında paralelliyin təsirini. Real API və ya LLM sürəti deyil.

**Coverage düzgün elmi cavab zəmanətidirmi?** Xeyr. Testdə hansı sətirlərin işlədiyini göstərir.

**İstinad varsa iddia doğrudurmu?** Nömrənin mövcudluğu və mənbənin iddianı sübut etməsi fərqlidir. Proqram struktur yoxlayır, tam elmi doğrulama etmir.

## Məşq

## v1.1.0 əlavələri

**Failover:** əsas web provayderi alınmasa konfiqurasiyadakı ikinci provayder sınanır. Chaos testi bunu açarsız göstərir. Tək DuckDuckGo sazlaması canlı failover nümayişi deyil.

**TokenBudget:** 60 saniyəlik pəncərədə konservativ təxmini token ehtiyatı ayırır. Bu hesablaşma sayğacı deyil. Testdə 7/10-dan sonra 4 token sorğusu 60 saniyə gözləyir. Həqiqi hesab/model TPM limitini operator sazlayır.

**UI:** CLI kimi eyni Researcher.ask metoduna gedir. Keş, provider çağırışları və validasiya interfeys koduna köçürülməyib.

**Real benchmark:** beş mövzu üzrə Wikipedia/arXiv, bir təkrar: 19.656s ardıcıl, 19.288s paralel (~1.02×). Bu, 3.01× sintetik ölçüdən ayrıdır. Şəbəkə və rate-limit qazancı azaldır.

**Nasaz JSON düzəlişi:** verilmiş parserin xarici cavabdan yaranan TypeError/AttributeError xətası AIService sərhədində mənbə xətasına çevrilir. Daxili proqramlaşdırma səhvləri ümumi except ilə gizlədilmir.

Hər üzv bir core testi seçsin, nəticəni əvvəlcədən izah edib işlətsin. Source timeout-u azaldıb davranışı izah edin. Cache expiry testində real sleep əvəzinə saatın niyə dəyişdirildiyini müzakirə edin: sürət və təkrarlana bilən nəticə.

## Son müdafiə qeydləri

121 test, 93.85% line coverage. Coverage düzgün elmi cavab faizi deyil.
Canlı Render nümunəsi: 23.21 saniyə, 3 mənbə və 3 istinad; bütün suallar üçün zəmanət yoxdur.
Problemləri docs/PROBLEMS_AND_SOLUTIONS.md üzrə simptom, həll və sübut ardıcıllığında izah edin.
Slayd 6-da real inteqrasiya problemləri var. Hər üç üzv danışmalı, başqasının modulunu da ümumi səviyyədə izah etməlidir.
