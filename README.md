# Mia Translate Backend

Mia Translate Backend, Mektup uygulamasında yazılı ve sesli mesajlardan elde edilen metinlerin hedef dile çevrilmesi için tasarlanan FastAPI tabanlı bir çeviri servisi backend projesidir.

Bu proje, Hugging Face üzerinde bulunan `mektup-mia/Mia-Translate` modelini kullanarak Google Cloud Vertex AI üzerinde çalışabilecek, kuyruk mekanizması, worker yapısı, batchleme, hata yönetimi ve mock client desteği bulunan production’a yakın bir MVP backend mimarisi oluşturmayı hedefler.

---

## Proje Amacı

Bu projenin amacı, Mektup uygulamasında kullanıcı mesajlarının farklı dillere çevrilebilmesi için ölçeklenebilir, test edilebilir ve Vertex AI entegrasyonuna hazır bir backend servis yapısı geliştirmektir.

Proje kapsamında yalnızca modeli çağıran basit bir API değil; gerçek ürün ortamına daha yakın olacak şekilde aşağıdaki bileşenleri içeren bir servis mimarisi hedeflenmektedir:

- FastAPI tabanlı REST API
- Sync ve async çeviri akışı
- Redis tabanlı queue/job store yapısı
- Worker ile arka plan çeviri işlemleri
- Worker tarafında micro-batching
- MockTranslationClient ile local geliştirme
- VertexAITranslationClient ile production entegrasyon hazırlığı
- Timeout, retry ve hata yönetimi
- Health ve readiness kontrolleri
- Docker ile çalıştırılabilir yapı
- Pytest ile test altyapısı
- OpenAPI/Swagger dokümantasyonu

---

## Kullanılacak Model

Projede kullanılacak model:

- Hugging Face repo: `mektup-mia/Mia-Translate`
- Temel model: `google/madlad400-3b-mt`
- Model tipi: Makine çevirisi
- Mimari: T5 encoder-decoder
- Yaklaşık parametre sayısı: 3B
- Hedef dil formatı: `<2tr>`, `<2en>`, `<2ar>` gibi dil tag'leri
- Giriş limiti: yaklaşık 512 token

Öncelikli desteklenecek diller:

- Türkçe
- İngilizce
- Arapça
- Almanca
- Fransızca

İlerleyen aşamalarda desteklenmesi planlanan diller:

- Rusça
- İspanyolca
- Japonca
- Korece
- Çince

---

## Teknoloji Stack

| Katman | Teknoloji |
|---|---|
| Backend Framework | FastAPI |
| Dil | Python |
| Veri Doğrulama | Pydantic |
| Config Yönetimi | pydantic-settings, .env |
| Queue / Job Store | Redis |
| Worker | Custom Python Worker |
| Batchleme | Worker tarafında micro-batching |
| Model Servisleme | Google Cloud Vertex AI |
| Local Test Model Client | MockTranslationClient |
| Container | Docker |
| Test | Pytest |
| API Dokümantasyonu | Swagger / OpenAPI |
| Loglama | Structured logging |

---

## Genel Mimari

```text
Mektup App / Client
        |
        v
FastAPI Backend
        |
        |-- Auth Middleware
        |-- Request Validation
        |-- Language Tag Mapping
        |-- Sync / Async Mode Decision
        |
        +-----------------------------+
        |                             |
        v                             v
Sync Translation Flow          Async Translation Flow
        |                             |
        v                             v
Translation Service            Redis Queue / Job Store
        |                             |
        v                             v
Translation Client             Translation Worker
        |                             |
        |                             |-- Micro-batching
        |                             |-- Retry
        |                             |-- Timeout handling
        |                             |-- Job status update
        |                             |
        +-------------+---------------+
                      |
                      v
          Translation Client Interface
                      |
          +-----------+------------+
          |                        |
          v                        v
MockTranslationClient     VertexAITranslationClient
          |                        |
          |                        v
          |              Vertex AI Endpoint
          |                        |
          |                        v
          |              Mia-Translate Model
          |
          v
Local/Test Response