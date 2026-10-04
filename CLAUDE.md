# Proje: Training Performance Dashboard (Strava Veri Pipeline'ı + Dashboard)

> Eski adları: "Data-Driven Sports Coaching" → "Sports Performance Dashboard" → **Training Performance
> Dashboard** (2026-10-03).

## Amaç
Ahmet Can Özdemir'in ("Acoz") kendi Strava aktivite verisi (koşu, CrossFit/HIIT) üzerinden veri odaklı
bir antrenman/performans dashboard'u. Proje [Portfolio_Website_Project](../Portfolio_Website_Project)
sitesinin Projeler bölümünde case study olarak sergilenecek — hem gerçek bir kişisel araç hem de iş
başvurularında gösterilecek uçtan uca bir BI/data engineering örneği.

## Kullanıcı Bağlamı
- Ahmet, TUSAŞ'ta Senior Data Analyst; teknoloji sektörüne (Data/BI/Product Analyst) geçiş hedefliyor
- Git/GitHub'a yeni — adımlar sade ve öğretici anlatılmalı
- Maraton koşucusu (İstanbul Maratonu 2025, 3:30)
- Strava/GCP/GitHub hesap işlemleri (app kaydı, faturalama, repo oluşturma) SADECE Ahmet'in hesabıyla
  yapılır; Claude rehberlik eder

## Kod Standartları
- `software-standards` skill'i (+ `references/python.md`, `references/nextjs.md`) bu projede varsayılan
- `todoist` skill'i Todoist işlemlerinde taksonomi/etiket kuralları için
- Lint/format: `ruff`; test: `pytest`; bağımlılıklar sürümü sabitlenmiş (`requirements-dev.txt`)
- Commit: Conventional Commits, her anlamlı adımdan sonra

## Mimari (2026-09-04, güncelleme 2026-10-03)
- **Platform:** GCP Always Free. Proje ID `training-performance-dashboard`, org `acozdemir1907-org`
  (org'a dokunulmayacak). Faturalama hesabı "Billing Acount" (`013BD0-702774-77F622`, TRY); eski
  "My Billing Account" kapalı. Bütçe alarmı 50 TL (~1 $), %50/%90/%100 e-posta. Bölge `europe-west1`,
  BigQuery dataset'i `training_performance` (EU), export bucket'ı
  `gs://training-performance-dashboard-public` (us-central1 — Cloud Storage ücretsiz kotası sadece ABD
  bölgelerinde; içerik zaten herkese açık özet JSON)
- **Veri kaynağı:** Strava API (OAuth, scope `activity:read_all`). 2023-09-19'dan bu yana ~476 aktivite.
  Nabız 2023–Eki 2025 arası neredeyse yok, Kasım 2025'ten beri neredeyse tam (arada nabızsız tekil
  aktiviteler olabiliyor, ör. 2026-10-03 21 km)
- **İşlem:** Tek Cloud Function `daily_pipeline` → Strava'dan tüm geçmişi çek (3 sayfa) → BigQuery'ye
  tam snapshot (WRITE_TRUNCATE load job; düzenlenen/silinen aktiviteleri de yakalar) → metrikleri
  hesapla → `dashboard.json`'u dışa aktar. Interval lap'leri bir kez çekilir, sonra BigQuery'den okunur.
  Cloud Function `daily-pipeline` (gen2, python312, europe-west1, 512Mi, max 1 instance), Cloud Scheduler
  job'ı `daily-pipeline` her gün 23:30 Europe/Istanbul, OIDC ile çağırır; kimliksiz çağrı 403.
  Deploy: `pipeline/deploy.sh` (idempotent; `.gcloudignore` `.env`/test/script'leri dışarıda tutar)
- **Yetkiler:** Servis hesapları `pipeline-runner` (fonksiyon), `scheduler-invoker` (sadece tetikleme,
  fonksiyonda run.invoker) ve `function-builder` (build; yeni projelerde varsayılan compute hesabına
  build yetkisi verilmiyor, `cloudbuild.builds.builder` rolüyle ayrı hesap).
  `pipeline-runner`: proje genelinde sadece `bigquery.jobUser` + `logging.logWriter`; dataset'te
  dataEditor, bucket'ta objectAdmin, 3 secret'ta accessor, refresh token secret'ında versionManager.
  Ahmet'in kullanıcısında yerel testler için bu hesabı taklit etme yetkisi (tokenCreator) var
- **Yerel çalıştırma:** `pipeline/` içinde `.venv/bin/python -m scripts.run_local` (ADC, pipeline-runner
  kimliğiyle; bu makinede Python'un CA paketi bazı hostları doğrulayamadığı için `truststore` kullanır)
- **Sırlar:** Secret Manager. Strava refresh token'ı değişebildiği için fonksiyon yenisini yeni secret
  versiyonu olarak yazar. Yerelde `pipeline/.env` (gitignore + `chmod 600`)
- **Depolama:** BigQuery `activities` (GPS/rota alanı yok) + `metrics` (günlük; dinlenme günleri 0 yük ile
  tarih omurgası)
- **Dashboard veri akışı:** Pipeline günlük, özetlenmiş `dashboard.json`'u herkese açık bir GCS
  dosyasına yazar; portfolyodaki Next.js sayfası bunu okur. Sitede kimlik bilgisi yok
- **Dashboard:** Next.js + Recharts, **Portfolio_Website_Project reposu içinde** proje detay sayfası
  (dashboard + case study). Portfolyo tasarım dili (warm-neutral + petrol mavisi `#2C6E8E`).
  "Powered by Strava" ibaresi zorunlu (Strava API şartı)
- **Faz 3 sunum katmanı:** Looker Studio (owner's credentials, ham veri kapalı). Tableau Public bu
  projenin parçası değil — ayrı "Tableau hands-on" task'ı, V1 sonrası
- **GitHub:** `ac-ozdemir/training-performance-dashboard` (public)
- **Public JSON gizliliği:** aktivite adları ve id'leri yayımlanmaz (konum/kişisel bilgi sızdırabilir);
  sadece yarış adları VDOT noktalarında etiket olarak çıkar
- **GPS/rota verisi hiç depolanmaz** (gizlilik kararı)

## Metrikler
- **TRIMP (Banister):** süre + ortalama nabız. Kişisel parametreler (`pipeline/config.py`): dinlenik
  nabız 48 (Garmin 1 yıllık ort.), max nabız 185 (Strava'da gözlenen tavan, Ahmet onayladı; 210 HIIT
  sensör hatası sayıldı), cinsiyet erkek. Banister dayanıklılık sporu için tasarlandı; CrossFit/HIIT'te
  yaklaşık — case study'de açıkça belirtilecek
- **LTHR 165** (Ahmet'in testi, 2026-10): LTHR bazlı nabız bölgeleri ve Faz 3'te TRIMP'i hrTSS ile
  çapraz kontrol için kullanılabilir
- **Nabızsız aktiviteler:** yük olarak 0 sayılır, tahmin yapılmaz (Ahmet kararı, 2026-10-04)
- **CTL/ATL/TSB:** 42/7 günlük EWMA, TSB = önceki günün CTL − ATL (TrainingPeaks konvansiyonu). Seri
  **2025-11-01'den** başlar (`LOAD_SERIES_START`, nabız kapsamının başladığı tarih); başlangıç CTL/ATL'i
  ilk 42/7 günün ortalama yüküyle doldurulur (sıfırdan yapay yükseliş olmasın diye). Export'taki günlük
  seri de buradan başlar
- **VDOT (Daniels & Gilbert):** iki kaynak, grafikte farklı işaretlerle
  - Yarışlar: Strava'da koşu tipi "Race" (`workout_type=1`) olanlar — başlığa "race" yazmaya gerek yok.
    **Kural:** "Race" sadece gerçekten yarış gibi koşulan yarışlar için kullanılır; pacer'lık edilen ya
    da keyif için koşulan yarışlar (ör. Bodrum Yarı Maratonu 2025, arkadaşına pacer'lık) normal koşu
    kalır. Karar tek yerde, Strava'da
  - Interval'ler: başlığında "interval" geçen koşuların tekrar lap'leri. Elenenler: lap'lerin %60+'ı
    1 km/1 mil olan seanslar (saatin otomatik lap'i — geçmiş "Interval Friday"lerin çoğu böyle).
    Kalanlarda lap'ler en büyük hız boşluğundan hızlı/yavaş gruba ayrılır; hızlı gruptaki 2.5–6 dk'lık
    lap'ler tekrar sayılır; tekrarın ortalama nabzı ≥ LTHR'nin %90'ı (~149) olmalı, en az 2 tekrar.
    Interval temposu ≈ VO2max hızı varsayımı; oturum değeri tekrarların medyanı. Kriterler 3 seansla
    kalibre edildi — yeni seanslar birikince (gerekirse Ahmet'in antrenman koçu agent'ıyla) gözden
    geçirilecek. Bugünkü veride tek geçerli interval: 2025-12-05 (47.5)
  - Aynı gün hem yarış hem interval varsa yarış önceliklidir. Yarışta süre olarak elapsed time kullanılır
- **Aktivite kategorileri:** Run/TrailRun/VirtualRun → koşu; HighIntensityIntervalTraining/Workout/
  WeightTraining/Crossfit → CrossFit; diğerleri → genel

## Faz Planı ve Durum
Kaynak: Todoist → "Side Projects" → **"Training Performance Dashboard"** section'ı
(projectId `6hQJcjr9826HXHmW`, sectionId `6hQJj3FjVxQc6rQW`). Güncel/otoriter kaynak Todoist'tir.

- **Faz 0 — Kurulum:** ✅ tamamlandı (Strava OAuth, GCP + faturalama + bütçe alarmı, API'ler, servis
  hesapları, Secret Manager, repo hijyeni, GitHub public repo + push)
- **Faz 1 — Veri pipeline'ı:** ✅ tamamlandı, 2026-10-04 canlıda (60 test). Ingestion + backfill,
  interval ayrıştırma, metrik job'ı, `dashboard.json` export, deploy, Scheduler
- **Faz 2 — Dashboard (5 Ekim):** ✅ Impeccable portfolyo reposuna kuruldu, `PRODUCT.md` + `DESIGN.md`
  ("Warm Precision") yazıldı (2026-10-04). ⏳ `/impeccable shape` ile sayfa planı (monospace font kararı
  dahil), Next.js
  sayfası (6 kart/grafik: VO2max & form özeti, CTL/ATL/TSB, haftalık TRIMP, pace, nabız, mesafe;
  genel/koşu/CrossFit filtreli)
- **Faz 3 — Doğrulama ve yayın (11 Ekim haftası):** hesaplamaları kişisel referanslarla doğrula,
  Looker Studio embed, case study
- **V2 Backlog:** manuel wellness check-in + AI insight + Garmin-özel metrikler

## Çalışma Modeli
- Claude geliştirici + PM rolünde, işin büyük kısmını fiilen yapar
- **Karar noktası Ahmet'tir:** geri dönüşü zor ya da zevk/tercih meselesi olan konularda seçenekler kısa
  gerekçeyle sunulur, onay beklenir. Saf teknik "nasıl" kararlarını Claude verir ve raporlar
- **Tek seferde bir iş kalemi:** sıradaki görevi sun, onay al, uygula, sonra geç
- Tamamlanan görevler Todoist'te kapatılır (karar özeti açıklamaya), kısmi ilerleme yorum olarak düşülür
- **Güvenlik:** secret'lar sohbete/çıktıya basılmaz, komut satırı argümanına değil stdin'e verilir;
  yerel secret dosyaları `chmod 600`; public repoya push öncesi geçmişte secret taraması yapılır

## Bir Sonraki Oturum İçin Not (2026-10-04 akşam)
Pipeline canlı, her gece 23:30'da çalışıyor; `dashboard.json` herkese açık
(`https://storage.googleapis.com/training-performance-dashboard-public/dashboard.json`, 1 saat
önbellek). Impeccable portfolyo reposunda kurulu; tasarım bağlamı portfolyodaki `PRODUCT.md` ve
`DESIGN.md`. Sıradaki: Faz 2 — `/impeccable shape` ile dashboard + case study sayfasını planla
(monospace font kararı dahil), sonra portfolyo reposunda kur (JSON şeması `pipeline/export/dashboard.py`,
`schema_version: 1`). Portfolyoda 2 commit henüz push edilmedi. Not: git geçmişini yeniden yazan komutlar Claude Code auto mode'da engelli —
gerekirse Ahmet kendisi çalıştırır.
