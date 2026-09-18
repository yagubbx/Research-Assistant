# Qarşılaşdığımız problemlər və həllər

Bu sənəd real müşahidələri ayırır: ehtimal olunan səbəb tam sübut olunmuş kök səbəb deyil.

| Problem | Müşahidə / səbəb | Həll | Sübut və məhdudiyyət |
|---|---|---|---|
| CLI: uncited sentence | Model bəzi cümlələrə istinad əlavə etmirdi | Synthesis prompt-a qayda, struktur validasiya və məhdud regenerasiya | test_se_citation_retry.py; istinadın olması elmi doğruluğu sübut etmir |
| Wikipedia boş nəticə | Uzun sual üçün yararlı excerpt gəlmirdi; tək səbəb kimi təsdiqlənməyib | topic_query ilə dar ingilis sual şablonlarının sadələşdirilməsi | test_se_search.py və 3 mənbəli canlı nümunə; bütün sorğular üçün zəmanət deyil |
| Web search gecikməsi | Xarici kitabxananın bloklayan işi ümumi vaxtı uzada bilərdi | 5 saniyə adapter timeout-u, seçilmiş backend, ayrıca dayandırılan worker | test_se_search.py, worker deadline testləri |
| Gemini model əlçatanlığı | 2.5 modelində 404, sonrakı seçimdə 503 müşahidə edildi | Təhlükəsiz status diaqnostikası; gemini-3.1-flash-lite ilə uğurlu yoxlama və default-ların uyğunlaşdırılması | render-live-verification.json; provayder sonradan yenə xəta verə bilər |
| Docker CMD xətası | İstifadəçinin logunda əmrin bir hissəsi tanınmırdı | verify_docker.cmd düzəldildi, yenidən icra edildi | docker-verification.txt: PASSED; ilkin dəqiq parser səbəbi ayrıca sübut olunmayıb |
| pytest quraşdırılmamışdı | İstifadəçinin .venv mühitində No module named pytest | requirements-dev.txt quraşdırma addımı sənədləşdirildi | Son agent yoxlaması 121 PASS; istifadəçinin həmin .venv mühitinin düzəldiyi ayrıca təsdiqlənməyib |
| Təqdim edilmiş ai/ faylları dəyişmişdi | İlkin Git nüsxəsi müəllimin iki faylından fərqlənirdi | ai/ bərpa edildi; adapter və prompt əlavələri researcher/ daxilinə keçirildi | ai-integrity.json, commit 758baec |
| README/PDF köhnəlmişdi | Test sayları və deploy statusu koddan geri qalmışdı | Sənədlər son yoxlama ilə yeniləndi, tarixi benchmarklar ayrıca saxlanıldı | final-verification.json və yenilənmiş hesabat |

## Müdafiədə izah qaydası

Simptom → müşahidə → dəyişiklik → test → qalan məhdudiyyət ardıcıllığını işlədin.
Saxta xəta, saxta review və ya edilməyən işə müəlliflik əlavə etməyin.
Offline rejim beş mövzulu sintetik demodur; internet olmadan yeni elmi araşdırma aparmır.
