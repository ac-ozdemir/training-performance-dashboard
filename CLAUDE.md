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
  (org'a dokunulmayacak), faturalama bağlı. Bölge `europe-west1`, BigQuery dataset'i EU
- **Veri kaynağı:** Strava API (OAuth, scope `activity:read_all`). 2023-09-19'dan bu yana ~474 aktivite,
  bunların ~%43'ünde nabız var
- **İşlem:** Tek Cloud Function `daily_pipeline` → Strava'dan çek → BigQuery'ye MERGE (idempotent) →
  metrikleri hesapla → dashboard verisini dışa aktar. Tek Cloud Scheduler job'ı, OIDC ile çağırır;
  fonksiyon herkese açık değil
- **Yetkiler:** Ayrı servis hesabı, en az yetki (sadece kendi dataset/secret/bucket'ı)
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
- **GitHub:** Pipeline reposu public olacak
- **GPS/rota verisi hiç depolanmaz** (gizlilik kararı)

## Metrikler
- **TRIMP (Banister):** süre + ortalama nabız. Kişisel parametreler: dinlenik nabız 48 (Garmin 1 yıllık
  ort.), max nabız ~185 (Strava'da gözlenen tavan; 210 HIIT ölçüm hatası sayıldı — Ahmet'in onayı
  bekleniyor), cinsiyet erkek. Banister dayanıklılık sporu için tasarlandı; CrossFit/HIIT'te yaklaşık —
  case study'de açıkça belirtilecek
- **CTL/ATL/TSB:** 42/7 günlük EWMA, TSB = önceki günün CTL − ATL (TrainingPeaks konvansiyonu)
- **VDOT (Daniels & Gilbert):** iki kaynak, grafikte farklı işaretlerle
  - Yarışlar: Strava'da koşu tipi "Race" (`workout_type=1`) olanlar — başlığa "race" yazmaya gerek yok
  - Interval'ler: başlığında "interval" geçen koşuların tekrar lap'leri — süresi 2.5–6 dk olan ve
    aktivitenin medyan lap temposundan belirgin hızlı lap'ler (ısınma/toparlanma/soğuma elenir).
    Interval temposu ≈ VO2max hızı varsayımıyla hesaplanır. Geçmiş interval'ler yeniden adlandırılmayacak
- **Aktivite kategorileri:** Run/TrailRun/VirtualRun → koşu; HighIntensityIntervalTraining/Workout/
  WeightTraining/Crossfit → CrossFit; diğerleri → genel

## Faz Planı ve Durum
Kaynak: Todoist → "Side Projects" → **"Training Performance Dashboard"** section'ı
(projectId `6hQJcjr9826HXHmW`, sectionId `6hQJj3FjVxQc6rQW`). Güncel/otoriter kaynak Todoist'tir.

- **Faz 0 — Kurulum:** ✅ Strava OAuth, ✅ GCP projesi + faturalama, ✅ repo hijyeni (README, ruff,
  pinli bağımlılıklar). ⏳ API'ler, servis hesabı, Secret Manager, bütçe alarmı, GitHub remote
- **Faz 1 — Veri pipeline'ı:** ✅ metrik fonksiyonları (26 test), ✅ BigQuery DDL. ⏳ ingestion + backfill,
  interval lap ayrıştırma, metrik job'ı, JSON export, deploy (`deploy.sh`), Scheduler
- **Faz 2 — Dashboard (4 Ekim):** Impeccable değerlendirmesi/kurulumu, monospace font kararı, Next.js
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

## Bir Sonraki Oturum İçin Not (2026-10-03 gece)
4 Ekim hedefi: pipeline canlı + dashboard sayfası. Sıra: GitHub remote + push → GCP API'leri, servis
hesabı, Secret Manager → ingestion + backfill → metrik job + JSON export → deploy + Scheduler →
Impeccable değerlendirmesi → dashboard sayfası. Ahmet'ten beklenenler: max nabız onayı, bütçe alarmı
onayı, geçmiş yarışları Strava'da "Race" tipine işaretleme.
