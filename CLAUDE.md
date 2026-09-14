# Proje: Data-Driven Sports Coaching (Strava Veri Pipeline'ı + Dashboard)

## Amaç
Ahmet Can Özdemir'in ("Acoz") kendi Strava aktivite verisi (koşu, CrossFit vb.) üzerinden
veri odaklı bir antrenman/performans dashboard'u kurması. Proje tamamlandığında
[Portfolio_Website_Project](../Portfolio_Website_Project) sitesinin Projeler bölümünde bir
case study olarak sergilenecek — yani bu proje hem gerçek bir kişisel araç hem de iş
başvurularında gösterilecek somut bir BI/data engineering örneği olacak.

## Kullanıcı Bağlamı
- Ahmet, TUSAŞ'ta Senior Data Analyst — Power BI/Grafana, KPI, otomatik raporlama deneyimi var,
  teknoloji sektörüne (Data/BI/Product Analyst) geçiş hedefliyor (bkz. Portfolio_Website_Project/CLAUDE.md)
- Git/GitHub'a yeni tanışıyor — adımlar sade ve öğretici anlatılmalı
- Maraton koşucusu (İstanbul Maratonu 2025, 3:30) — projenin gerçek verisi kendi koşu/antrenman geçmişi olacak
- **Önemli:** Strava Developer portalında API app kaydı ve GCP faturalama hesabı açma gibi adımlar
  SADECE Ahmet'in kendi hesabıyla yapılabilir. Claude bu adımlarda rehberlik eder, ekran görüntüsü/
  komut bazlı yardımcı olur ama işlemi bizzat gerçekleştiremez.

## Mimari (karar verildi — 2026-09-04)
- **Platform:** GCP, **Always Free** katmanında kalacak şekilde kurulum
- **Veri kaynağı:** Strava API (OAuth), batch load — tek bir Cloud Scheduler job'ı
- **Depolama:** BigQuery — `activities` + `metrics` tabloları
- **İşlem:** Cloud Functions (ingestion + günlük metrik hesaplama)
- **Sırlar:** Secret Manager (Strava client id/secret/refresh token)
- **Metrikler:** VO2max (Daniels VDOT formülü), TRIMP (Banister), ATL/CTL/TSB — saf fonksiyonlar,
  unit test ile doğrulanacak
- **Dashboard:** Next.js sayfası + Recharts — **Portfolio_Website_Project reposu içinde**, "projects"
  grid'i altında bu projeye özel bir detay sayfası olarak (dashboard + case study aynı sayfada).
  Portfolyo'nun tasarım diline (warm-neutral zemin + petrol mavisi `#2C6E8E`) uyumlu olacak.
- **İkincil sunum katmanları (Faz 3):** Aynı BigQuery verisi üzerine Tableau Public (native
  connector, herkese açık) ve Looker Studio (owner's credentials, ham veri gizli) — ikisi de ücretsiz
- **GPS/rota verisi hiçbir sunum katmanında gösterilmeyecek** (gizlilik kararı)

## Faz Planı
Kaynak: Todoist → "Side Projects" → **"Data-Driven Sports Coaching"** section'ı
(projectId `6hQJcjr9826HXHmW`, sectionId `6hQJj3FjVxQc6rQW`). Bu dosya kopya değil, oradaki
görevlerin özetidir — güncel/otoriter kaynak her zaman Todoist'tir.

- **Faz 0 — Kurulum**
  - [p1] GCP projesini kur (BigQuery, Cloud Functions, Secret Manager, Cloud Scheduler)
  - [p2] Kullanıcı tarafı kurulumlar + Strava OAuth bağlantısı (Strava Developer app kaydı,
    GCP faturalama hesabı, OAuth consent → koddan test)
- **Faz 1 — Veri pipeline'ı**
  - [p2] BigQuery şema tasarımı + ingestion Cloud Function (Strava hesabı başından itibaren
    tüm geçmişin backfill'i)
  - [p2] Metrik hesaplama fonksiyonları (unit test'li) + Cloud Scheduler ile günlük otomatik çalıştırma
- **Faz 2 — Dashboard**
  - [p3] Next.js dashboard sayfası + Recharts: 6 kart/grafik (VO2max & form özeti, CTL/ATL/TSB,
    haftalık TRIMP, pace trendi, nabız trendi, mesafe trendi), genel/koşu/CrossFit filtreli
  - [p3] Next.js proje detay sayfası (dashboard + case study) + son 12 haftayı döndüren API katmanı
- **Faz 3 — Doğrulama ve yayın**
  - [p3] Hesaplamaları kişisel referanslarla doğrula, Tableau Public + Looker Studio embed'lerini
    kur, case study yazısını yaz ve yayına al
- **V2 Backlog (şimdilik kapsam dışı)**
  - [p4] Manuel wellness check-in + AI insight + Garmin-özel metrikler — n8n projesindeki
    "veri çek → analiz et → AI ile insight üret" kalıbının buraya uyarlanması. Aynı beceri iki
    projede tekrar edilmesin diye V1'e dahil edilmedi.

## Çalışma Modeli
Portfolio_Website_Project ile aynı prensipler:
- Claude geliştirici + PM rolünü üstlenir, işin büyük kısmını fiilen yapar
- **Karar noktası kullanıcıdır:** geri dönüşü zor veya zevk/tercih meselesi olan konularda
  (üçüncü parti servis seçimi, dashboard'da hangi metriklerin öne çıkarılacağı, case study anlatımı vb.)
  Claude seçenekleri kısa gerekçeleriyle sunar ve onay bekler
- Saf teknik "nasıl" kararlarında (klasör yapısı, kütüphane detayları) Claude kendi kararını verip raporlar
- **Tek seferde bir iş kalemi:** genel bir "devam et" onayı, arka arkaya birden fazla farklı görevi
  sessizce uygulama izni olarak alınmaz — sıradaki görevi sun, onay al, uygula, sonra geç
- Her anlamlı adımdan sonra kısa ve açıklayıcı commit mesajıyla commit atılmalı (Ahmet GitHub'a yeni tanışıyor)

## Proje Takibi
Görevler Todoist'te **"Side Projects" → "Data-Driven Sports Coaching"** section'ında tutulur
(projectId `6hQJcjr9826HXHmW`, sectionId `6hQJj3FjVxQc6rQW`). Bir görev tamamlandığında Todoist'te
işaretlenmeli; yeni iş kalemleri ortaya çıktığında oraya eklenmelidir.

## Bir Sonraki Oturum İçin Not
Şu an açık en yüksek öncelikli görev **Faz 0 → "GCP projesini kur"** (p1). Ondan sonra sırada
Strava OAuth bağlantısı ve Faz 1 (BigQuery şema + ingestion) var. Telefon/Remote Control
üzerinden çalışırken Strava/GCP hesap adımlarında Ahmet'in ekranından bilgi/onay istemek gerekecek.
