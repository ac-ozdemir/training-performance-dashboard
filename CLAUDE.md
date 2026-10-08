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
- **CTL/ATL/TSB:** 42/7 günlük EWMA, TSB = aynı günün CTL − ATL (2026-10-08 kararı: sayfadaki Form = Fitness − Fatigue tutarlı olsun diye; TrainingPeaks'in "önceki gün" konvansiyonu bırakıldı). Seri
  **2025-11-01'den** başlar (`LOAD_SERIES_START`, nabız kapsamının başladığı tarih); başlangıç CTL/ATL'i
  ilk 42/7 günün ortalama yüküyle doldurulur (sıfırdan yapay yükseliş olmasın diye). Export'taki günlük
  seri de buradan başlar
- **VDOT (Daniels & Gilbert):** üç kaynak, grafikte farklı işaretlerle (yarış dolu daire, interval
  halka, tempo kare). Etiketlerin ikisi de Ahmet'in Strava'da seçtiği koşu tipi — karar tek yerde, Strava'da
  - Yarışlar: koşu tipi "Race" (`workout_type=1`). **Kural:** "Race" sadece gerçekten yarış gibi koşulan
    yarışlar için; pacer'lık edilen ya da keyif için koşulanlar (ör. Bodrum Yarı Maratonu 2025) normal
    koşu kalır. Süre olarak elapsed time
  - Interval ve tempo: koşu tipi **"Workout"** (`workout_type=3`, 2026-10-08 kararı; eski "başlıkta
    interval" kuralı kaldırıldı). `pipeline/metrics/workouts.py` lap yapısından ayırt eder; lap'ler en büyük
    hız boşluğundan hızlı/yavaş gruba ayrılır. Saatin yapılandırılmış antrenmanları her adım için lap
    attığından elle lap kadar iyi çalışır
    - **Interval:** hızlı gruptaki 2.5–6 dk'lık lap'ler, en az 2 tekrar, tekrar nabzı ≥ %90 LTHR (~149);
      otomatik 1 km/1 mil lap'li seanslar elenir; I tempo ≈ vVO2max; oturum değeri tekrarların medyanı
    - **Tempo:** hızlı gruptaki 10–40 dk'lık blok(lar), toplam ≥ 15 dk, zaman ağırlıklı nabız ≥ %95 LTHR
      (~157); T tempo = 60 dk yarış temposu sayılır. Isınmadaki otomatik km lap'leri tempo'yu elemez
    - **LTHR testi** (30 dk tam efor) tempo olarak okunuyor ve ~2.4 yüksek çıkıyor (53.2; 30 dk yarış
      olarak ≈ 50.8) — Ahmet'in kararıyla tempo olarak kalıyor, case study'de not edilecek
  - Aynı gün yarış ile workout çakışırsa yarış öncelikli
  - Kural doğrulaması gerçek seanslarla yapıldı (`docs/validation-2026-10-08.md` §5): Ekim interval 50.9,
    tempo 51.7, son yarış 51.2 ile tutarlı
- **Aktivite kategorileri:** Run/TrailRun/VirtualRun → koşu; HighIntensityIntervalTraining/Workout/
  WeightTraining/Crossfit → CrossFit; diğerleri → genel
- **Doğrulama (2026-10-08, `docs/validation-2026-10-08.md`, `pipeline/analysis/validate_metrics.py`):**
  TRIMP ↔ hrTSS (ortalama nabız yaklaşımı, LTHR 165) aktivite bazında r = 0.955 (koşu 0.975, CrossFit
  0.951), TRIMP/hrTSS medyanı 1.09; CTL r = 0.959, TSB r = 0.973, günlerin %88'inde aynı form bölgesi
  → sayfadaki TSS ölçekli bölge eşikleri (−30/−10/+5) TRIMP'e uyuyor. Garmin VO2max (güncel 59) aynı
  yarıştan sonra race VDOT'un ~3 puan üstünde (fizyolojik vs. performansa dayalı tahmin); sayfada
  "Running fitness (VDOT)" olarak doğru etiketli, "VO2max" denmiyor

## Faz Planı ve Durum
Kaynak: Todoist → "Side Projects" → **"Training Performance Dashboard"** section'ı
(projectId `6hQJcjr9826HXHmW`, sectionId `6hQJj3FjVxQc6rQW`). Güncel/otoriter kaynak Todoist'tir.

- **Faz 0 — Kurulum:** ✅ tamamlandı (Strava OAuth, GCP + faturalama + bütçe alarmı, API'ler, servis
  hesapları, Secret Manager, repo hijyeni, GitHub public repo + push)
- **Faz 1 — Veri pipeline'ı:** ✅ tamamlandı, 2026-10-04 canlıda (60 test). Ingestion + backfill,
  interval ayrıştırma, metrik job'ı, `dashboard.json` export, deploy, Scheduler
- **Faz 2 — Dashboard:** ✅ tamamlandı (4-5 Ekim, portfolyo reposunda), yayında:
  `https://acozdemir.com/projects/training-performance-dashboard`. Akış sonradan "önce dashboard"
  olarak değişti; 6 grafik + filtreler, Powered by Strava logosu, audit + polish, OG görseli. Hata
  alarmı kuruldu ve 2026-10-08'de uçtan uca doğrulandı (`pipeline/alerting/`)
- **Faz 3 — Doğrulama ve yayın:** ✅ doğrulama (TRIMP ↔ hrTSS, Garmin kıyası, Workout/tempo kuralları
  gerçek seanslarla — 2026-10-08). Aynı gece: Workout etiketi + tempo VDOT, aynı gün TSB, sayfada
  Fatigue göstergesi (yayında). ⏳ Looker Studio embed, case study metni
- **V2 Backlog:** manuel wellness check-in + AI insight + Garmin-özel metrikler

## Hangi İş Hangi Klasörde (2026-10-04)
- **Bu repo (Training_Performance_Dashboard_Project):** veri tarafı — pipeline, metrikler, GCP, deploy,
  alarm, Faz 3 doğrulama, Looker Studio'nun BigQuery tarafı, README. Proje kararlarının ana kaydı bu
  CLAUDE.md'dir
- **Portfolio_Website_Project:** görünen taraf — dashboard + case study sayfası (Faz 2, case study metni).
  Impeccable'ın skill'i ve hook'u yalnızca o klasörde açılan oturumda çalıştığı için arayüz işi orada,
  ayrı sohbette yapılır; bu repoya gerektiğinde ek klasör erişimiyle bakılır
- İki repo arasındaki sözleşme `dashboard.json` (`pipeline/export/dashboard.py`, `schema_version`).
  Sayfa yeni bir alana ihtiyaç duyarsa değişiklik burada yapılır, sürüm numarası artırılır
- Görevlerin tek doğru kaynağı Todoist; hangi klasörde çalışılırsa çalışılsın bu CLAUDE.md güncel tutulur

## Çalışma Modeli
- Claude geliştirici + PM rolünde, işin büyük kısmını fiilen yapar
- **Karar noktası Ahmet'tir:** geri dönüşü zor ya da zevk/tercih meselesi olan konularda seçenekler kısa
  gerekçeyle sunulur, onay beklenir. Saf teknik "nasıl" kararlarını Claude verir ve raporlar
- **Tek seferde bir iş kalemi:** sıradaki görevi sun, onay al, uygula, sonra geç
- Tamamlanan görevler Todoist'te kapatılır (karar özeti açıklamaya), kısmi ilerleme yorum olarak düşülür
- **Güvenlik:** secret'lar sohbete/çıktıya basılmaz, komut satırı argümanına değil stdin'e verilir;
  yerel secret dosyaları `chmod 600`; public repoya push öncesi geçmişte secret taraması yapılır

## Bir Sonraki Oturum İçin Not (2026-10-08 akşam)
Pipeline canlı ve sağlıklı (479 aktivite), hata alarmı doğrulandı, Faz 3 doğrulaması bitti. Kalanlar:
Looker Studio raporu (Ahmet'in Google hesabıyla, Claude rehberliğinde; BigQuery tarafı bu repoda) ve case
study metni (portfolyo reposunda; malzeme `docs/validation-2026-10-08.md` ve README'deki tasarım
kararları). Açık: 2025-12-05 ve 2026-03-27 yapılandırılmış interval'leri Strava'da Workout olarak
etiketlenirse VDOT'a 47.5 ve 46.5 eklenir (Ahmet'in kararı).

Bilinen ortam sorunları:
- Git geçmişini yeniden yazan komutlar Claude Code auto mode'da engelli — gerekirse Ahmet kendisi çalıştırır
- Documents klasörü iCloud'da ve "Mac depolamayı optimize et" açık: portfolyonun `node_modules`'ındaki
  binlerce dosya yalnız bulutta duruyor, ESLint/derleme bu yüzden takılabiliyor (2026-10-08). Yayından önce
  güvence Vercel'in kendi derlemesi; kalıcı çözüm Ahmet'in kararına bırakıldı
- Strava okuma limiti 100 istek / 15 dk, 1000 / gün: geniş taramalar `analysis/` script'leriyle yavaşlatılarak
  ve 23:30 gece çalışmasının penceresinden uzak çalıştırılmalı
