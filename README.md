# Mia Translate Backend

Mia Translate Backend, Mektup uygulamasında kullanılacak çeviri altyapısı için geliştirilen FastAPI tabanlı backend servisidir.

Bu proje, `mektup-mia/Mia-Translate` modelinin production’a yakın bir backend mimarisiyle kullanılabilmesi için hazırlanmıştır. Amaç yalnızca bir model çağıran API yazmak değil; çeviri isteklerini doğrulayan, sıraya alan, arka planda worker ile işleyen, batchleme ve retry mekanizmalarıyla desteklenen, Docker ile çalıştırılabilen ve farklı model servisleme seçeneklerine hazır bir servis mimarisi kurmaktır.

Mevcut MVP sürümünde backend akışı local geliştirme ve test için `MockTranslationClient` ile çalışmaktadır. Model çağırma katmanı soyutlandığı için NVIDIA Triton, CTranslate2 veya Google Cloud Vertex AI entegrasyonları mevcut API, Redis queue ve worker mimarisi bozulmadan eklenebilir.

---

## İçindekiler

- [Proje Amacı](#proje-amacı)
- [Genel Mimari](#genel-mimari)
- [Temel Özellikler](#temel-özellikler)
- [Model Servisleme Yaklaşımı](#model-servisleme-yaklaşımı)
- [Klasör Yapısı](#klasör-yapısı)
- [API Endpointleri](#api-endpointleri)
- [Async Job ve Worker Akışı](#async-job-ve-worker-akışı)
- [Worker Batchleme](#worker-batchleme)
- [Retry ve Failed Job Yönetimi](#retry-ve-failed-job-yönetimi)
- [Docker ile Çalıştırma](#docker-ile-çalıştırma)
- [Local Geliştirme](#local-geliştirme)
- [Testler](#testler)
- [Environment Değişkenleri](#environment-değişkenleri)
- [Mevcut MVP Kapsamı](#mevcut-mvp-kapsamı)
- [Geliştirme Yol Haritası](#geliştirme-yol-haritası)

---

## Proje Amacı

Mektup uygulamasında kullanıcı mesajlarının farklı dillere çevrilebilmesi için ölçeklenebilir ve geliştirilebilir bir backend altyapısı hazırlanması hedeflenmektedir.

Bu projede odaklanılan temel ihtiyaçlar:

- Tekil çeviri isteği alabilmek
- Batch çeviri isteği alabilmek
- Uzun sürebilecek işleri async job olarak kuyruğa almak
- Redis üzerinde job durumlarını takip etmek
- Worker ile arka planda job işlemek
- Worker tarafında micro-batching uygulamak
- Geçici hata durumlarında retry mekanizması kullanmak
- Model çağırma katmanını Mock, Triton, CTranslate2 ve Vertex AI seçeneklerine hazır hale getirmek
- Docker ile API, Worker ve Redis servislerini birlikte çalıştırabilmek

---

## Genel Mimari

```text
Client / Mektup App
        |
        v
FastAPI API
        |
        |-- GET  /health
        |-- GET  /ready
        |-- POST /api/v1/translate
        |-- POST /api/v1/translate/batch
        |-- GET  /api/v1/jobs/{job_id}
        |
        v
Translation Service
        |
        |-- Validation Service
        |-- Language Service
        |-- Client Factory
        |
        +-----------------------------+
        |                             |
        v                             v
Sync Flow                      Async Flow
        |                             |
        v                             v
Translation Client             Redis Job Store
        |                             |
        |                             v
        |                      Redis Queue
        |                             |
        |                             v
        |                      Translation Worker
        |                             |
        |                             v
        +--------------------- Translation Client
                                      |
                                      v
                     Mock / Triton / CTranslate2 / Vertex AI
```

Bu mimaride API katmanı, iş mantığı, Redis job store, Redis queue, worker ve model client katmanları birbirinden ayrılmıştır. Böylece model servisleme yöntemi değişse bile API ve worker akışı büyük ölçüde korunur.

---

## Temel Özellikler

- FastAPI tabanlı REST API
- Swagger/OpenAPI dokümantasyonu
- `.env` tabanlı merkezi config yönetimi
- Sync çeviri akışı
- Async job oluşturma
- Redis tabanlı job store
- Redis queue ile sıraya alma
- Worker ile arka planda işleme
- Worker-side batch processing
- Retry / failed job yönetimi
- MockTranslationClient ile local test edilebilir yapı
- Triton, CTranslate2 ve Vertex AI client iskeletleri
- Docker Compose ile API + Worker + Redis çalıştırma
- Pytest test altyapısı

---

## Kullanılan Model

Planlanan model:

- Hugging Face repo: `mektup-mia/Mia-Translate`
- Temel model: `google/madlad400-3b-mt`
- Model tipi: makine çevirisi
- Mimari: T5 encoder-decoder
- Yaklaşık parametre sayısı: 3B
- Hedef dil formatı: `<2tr>`, `<2en>`, `<2ar>` gibi dil tag’leri
- Giriş limiti: yaklaşık 512 token

Bu backend mimarisi Mia-Translate modelini farklı servisleme seçenekleriyle kullanabilecek şekilde hazırlanmıştır. Mevcut local geliştirme akışında gerçek model inference yerine `MockTranslationClient` kullanılmaktadır.

---

## Model Servisleme Yaklaşımı

Projede model çağırma katmanı `TranslationClient` arayüzü üzerinden soyutlanmıştır.

Bu sayede servis ve worker doğrudan belirli bir model servisleme yöntemine bağımlı değildir.

Desteklenen client seçenekleri:

```text
mock
triton
ctranslate2
vertex
```

Aktif client `.env` üzerinden belirlenir:

```env
TRANSLATION_CLIENT=mock
```

### MockTranslationClient

Local geliştirme ve test ortamında kullanılır. Gerçek çeviri yapmaz, ancak backend akışının çalıştığını doğrulamak için mock cevap döndürür.

Örnek çıktı:

```text
[mock-<2en>] Merhaba
```

### TritonTranslationClient

NVIDIA Triton Inference Server entegrasyonu için hazırlanmış client iskeletidir.

Bu client, Triton model repository yapısı ve model input/output şeması netleştirildiğinde gerçek inference çağrısı yapacak şekilde genişletilebilir.

### CTranslate2TranslationClient

Mia-Translate modelinin CTranslate2 formatına dönüştürülmüş versiyonunu kullanmak için hazırlanmıştır.

CTranslate2, model inference performansını artırmak için değerlendirilecek bir seçenektir. Bu client aktif edilmeden önce modelin CTranslate2 formatına dönüştürülmesi gerekir.

### VertexAITranslationClient

Google Cloud Vertex AI endpoint entegrasyonu için hazırlanmıştır.

Vertex AI project, location, endpoint ve credential bilgileri sağlandığında aynı `TranslationClient` arayüzü üzerinden gerçek endpoint çağrısı eklenebilir.

---

## Klasör Yapısı

```text
app/
  api/
    v1/
      endpoints/
        health.py
        jobs.py
        translate.py
      router.py

  clients/
    base.py
    mock_client.py
    triton_client.py
    ctranslate2_client.py
    vertex_ai_client.py
    factory.py

  core/
    config.py
    exceptions.py

  models/
    translation_job.py

  queue/
    redis_client.py
    job_store.py
    translation_queue.py

  schemas/
    job.py
    translation.py

  services/
    job_service.py
    language_service.py
    translation_service.py
    validation_service.py

  utils/
    id_generator.py

  workers/
    batcher.py
    translation_worker.py

docker/
  Dockerfile.api
  Dockerfile.worker

tests/
docker-compose.yml
requirements.txt
README.md
```

### Önemli Klasörler

`app/api/`  
FastAPI endpointlerinin bulunduğu katmandır.

`app/clients/`  
Model servisleme clientlarının bulunduğu katmandır. Mock, Triton, CTranslate2 ve Vertex AI seçenekleri burada konumlanır.

`app/core/`  
Config ve özel hata sınıfları gibi çekirdek yapıların bulunduğu bölümdür.

`app/models/`  
İç veri modellerinin bulunduğu katmandır. Redis’te saklanan translation job modeli burada tanımlanır.

`app/queue/`  
Redis bağlantısı, Redis job store ve Redis queue yapıları burada bulunur.

`app/schemas/`  
API request/response modelleri burada tanımlanır.

`app/services/`  
İş mantığının bulunduğu katmandır. Translation, validation, language ve job servisleri burada yer alır.

`app/workers/`  
Redis queue’dan job alan ve arka planda çeviri işleyen worker yapısı burada bulunur.

`tests/`  
Pytest testlerinin bulunduğu klasördür.

---

## API Endpointleri

### Health Check

```http
GET /health
```

Servisin ayakta olup olmadığını kontrol eder.

Örnek response:

```json
{
  "status": "ok",
  "service": "mia-translate-backend"
}
```

---

### Readiness Check

```http
GET /ready
```

Servisin iş kabul etmeye hazır olup olmadığını kontrol eder.

Kontrol edilen başlıklar:

- Config okunabiliyor mu?
- Aktif translation client nedir?
- Redis bağlantısı çalışıyor mu?
- Vertex config değerleri tanımlı mı?

Örnek response:

```json
{
  "status": "ready",
  "service": "mia-translate-backend",
  "environment": "docker",
  "checks": {
    "config": "ok",
    "translation_client": "mock",
    "redis": "ok",
    "redis_url_configured": true,
    "vertex_configured": false
  }
}
```

---

### Tekil Çeviri

```http
POST /api/v1/translate
```

Sync veya async modda tekil çeviri isteği alır.

#### Sync Request

```json
{
  "text": "Merhaba",
  "source_lang": "tr",
  "target_lang": "en",
  "mode": "sync"
}
```

#### Sync Response

```json
{
  "request_id": "req_...",
  "mode": "sync",
  "status": "completed",
  "source_lang": "tr",
  "target_lang": "en",
  "translated_text": "[mock-<2en>] Merhaba",
  "job_id": null
}
```

#### Async Request

```json
{
  "text": "Merhaba",
  "source_lang": "tr",
  "target_lang": "en",
  "mode": "async"
}
```

#### Async Response

```json
{
  "request_id": "req_...",
  "mode": "async",
  "status": "queued",
  "source_lang": "tr",
  "target_lang": "en",
  "translated_text": null,
  "job_id": "job_..."
}
```

---

### Batch Çeviri

```http
POST /api/v1/translate/batch
```

Birden fazla metni tek request içinde alır.

Örnek request:

```json
{
  "items": [
    {
      "text": "Merhaba",
      "source_lang": "tr",
      "target_lang": "en"
    },
    {
      "text": "Nasılsın?",
      "source_lang": "tr",
      "target_lang": "en"
    }
  ],
  "mode": "sync"
}
```

Örnek response:

```json
{
  "request_id": "req_...",
  "mode": "sync",
  "status": "completed",
  "items": [
    {
      "item_index": 0,
      "status": "completed",
      "source_lang": "tr",
      "target_lang": "en",
      "translated_text": "[mock-<2en>] Merhaba",
      "job_id": null,
      "error": null
    },
    {
      "item_index": 1,
      "status": "completed",
      "source_lang": "tr",
      "target_lang": "en",
      "translated_text": "[mock-<2en>] Nasılsın?",
      "job_id": null,
      "error": null
    }
  ],
  "job_ids": []
}
```

---

### Job Durumu Sorgulama

```http
GET /api/v1/jobs/{job_id}
```

Async olarak kuyruğa alınan job’ın durumunu döndürür.

Olası durumlar:

```text
queued
processing
completed
failed
```

Örnek response:

```json
{
  "job_id": "job_...",
  "status": "completed",
  "source_lang": "tr",
  "target_lang": "en",
  "translated_text": "[mock-<2en>] Merhaba",
  "error": null,
  "retry_count": 0
}
```

---

## Async Job ve Worker Akışı

Async modda gelen çeviri isteği doğrudan işlenmez.

Akış:

```text
1. API request alınır
2. Request validation yapılır
3. job_id üretilir
4. Job Redis’e kaydedilir
5. job_id Redis queue’ya eklenir
6. API kullanıcıya job_id döner
7. Worker queue’dan job alır
8. Job status processing yapılır
9. TranslationClient ile çeviri yapılır
10. Job status completed yapılır
11. Sonuç Redis’e yazılır
12. Kullanıcı GET /jobs/{job_id} ile sonucu alır
```

Bu yapı uzun sürebilecek çeviri işlemlerinin API request süresini bloklamadan arka planda yürütülmesini sağlar.

---

## Worker Batchleme

Worker tek tek job işlemek yerine kısa süreli bir batch toplama penceresi kullanır.

Ayarlar:

```env
MAX_BATCH_SIZE=8
MAX_WAIT_MS=200
```

Örnek davranış:

```text
Queue length: 3
Worker --once çalışır
Processed: 3
Queue length: 0
```

Bu yapı özellikle çok sayıda istek geldiğinde model çağrılarını daha kontrollü ve verimli hale getirmek için hazırlanmıştır.

---

## Retry ve Failed Job Yönetimi

Worker job işlerken hata alırsa job hemen kaybolmaz.

Akış:

```text
Hata oluşur
  |
  |-- retry_count < MAX_RETRIES ise:
  |       retry_count artırılır
  |       status queued yapılır
  |       job tekrar queue’ya eklenir
  |
  |-- retry_count >= MAX_RETRIES ise:
          status failed yapılır
          error bilgisi kaydedilir
```

Retry ayarı:

```env
MAX_RETRIES=3
```

Bu yapı geçici model veya network hatalarında job’ın tekrar denenmesini sağlar.

---

## Docker ile Çalıştırma

Proje Docker Compose ile API, Worker ve Redis servislerini birlikte ayağa kaldırabilir.

### Build ve Çalıştırma

```bash
docker compose up --build
```

Arka planda çalıştırmak için:

```bash
docker compose up --build -d
```

Servisleri kontrol etmek için:

```bash
docker ps
```

Beklenen container’lar:

```text
mia-translate-api
mia-translate-worker
mia-translate-redis
```

### API

```text
http://127.0.0.1:8000/docs
```

### Ready Check

```text
http://127.0.0.1:8000/ready
```

### Redis Queue Kontrolü

```bash
docker exec mia-translate-redis redis-cli LLEN translation_jobs:queue
```

---

## Local Geliştirme

Sanal ortam oluşturma:

```bash
python -m venv venv
```

Windows PowerShell için aktif etme:

```powershell
.\venv\Scripts\Activate.ps1
```

Bağımlılıkları yükleme:

```bash
pip install -r requirements.txt
```

Redis’i Docker ile çalıştırma:

```bash
docker compose up -d redis
```

API çalıştırma:

```bash
uvicorn app.main:app --reload
```

Worker’ı tek batch için çalıştırma:

```bash
python -m app.workers.translation_worker --once
```

Worker’ı sürekli çalıştırma:

```bash
python -m app.workers.translation_worker
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

## Testler

Testleri çalıştırmak için:

```bash
pytest
```

Test edilen başlıklar:

- Health endpoint
- Readiness endpoint
- Translation validation
- Language tag üretimi
- Sync translate endpoint
- Batch translate endpoint
- Async job oluşturma
- Job status sorgulama
- Redis job/queue akışı
- Worker job processing
- Worker batch processing
- Retry / failed handling
- Client factory
- Mock / Triton / CTranslate2 / Vertex client seçimi

Son doğrulamada tüm testler başarılı geçmiştir.

---

## Environment Değişkenleri

Örnek `.env`:

```env
APP_NAME=mia-translate-backend
APP_ENV=local
API_PREFIX=/api/v1

TRANSLATION_CLIENT=mock

REDIS_URL=redis://localhost:6380/0

MAX_BATCH_SIZE=8
MAX_WAIT_MS=200
MAX_INPUT_CHARACTERS=2000
MAX_BATCH_ITEMS=32
TRANSLATION_TIMEOUT_SECONDS=30
MAX_RETRIES=3

API_AUTH_ENABLED=false
API_BEARER_TOKEN=dev-secret

TRITON_URL=http://localhost:8001
TRITON_MODEL_NAME=mia_translate
TRITON_TIMEOUT_SECONDS=30

CTRANSLATE2_MODEL_PATH=./models/mia-translate-ct2
CTRANSLATE2_DEVICE=cpu
CTRANSLATE2_COMPUTE_TYPE=int8

VERTEX_PROJECT_ID=
VERTEX_LOCATION=
VERTEX_ENDPOINT_ID=
```

Docker Compose içinde API ve Worker servisleri Redis’e şu adresle bağlanır:

```env
REDIS_URL=redis://redis:6379/0
```

Local geliştirmede ise host üzerinden:

```env
REDIS_URL=redis://localhost:6380/0
```

---

## Mevcut MVP Kapsamı

Bu MVP sürümünde çeviri backend’inin ana servis mimarisi hazırlanmıştır.

Hazır olan ana parçalar:

- FastAPI API katmanı
- Health ve readiness kontrolleri
- Request/response schema’ları
- Dil doğrulama ve hedef dil tag üretimi
- Sync çeviri akışı
- Batch çeviri akışı
- Async job oluşturma
- Redis job store
- Redis queue
- Worker
- Worker-side batch processing
- Retry / failed job handling
- Client factory
- Mock, Triton, CTranslate2 ve Vertex AI client iskeletleri
- Docker ile API + Worker + Redis çalıştırma
- Pytest test altyapısı

Bu sürümde local geliştirme ve backend akış testleri için `MockTranslationClient` aktif kullanılmaktadır. Triton, CTranslate2 ve Vertex AI client yapıları mimariye eklenmiş ve gerçek model servisleme ortamı netleştiğinde aktif edilebilecek şekilde hazırlanmıştır.

---

