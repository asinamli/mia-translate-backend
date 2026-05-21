# Mia Translate Backend

Mia Translate Backend, Mektup uygulamasında kullanılacak çeviri altyapısı için geliştirilen FastAPI tabanlı backend servisidir.

Bu proje yalnızca bir model çağıran basit API yapısı değildir. Çeviri isteklerini doğrulayan, sync/async çalışabilen, Redis queue üzerinden job yönetimi yapan, worker ile arka planda işleyen, batchleme ve retry mekanizmaları içeren, Docker ile ayağa kaldırılabilen ve farklı model servisleme seçeneklerine hazır bir backend mimarisi olarak tasarlanmıştır.

Backend varsayılan olarak `MockTranslationClient` ile hızlı şekilde test edilebilir. Bunun yanında CTranslate2 tabanlı MADLAD/Mia model inference akışı local ortamda doğrulanmıştır. Model çağırma katmanı soyutlandığı için CTranslate2, NVIDIA Triton veya Google Cloud Vertex AI seçenekleri mevcut API, Redis queue ve worker mimarisi bozulmadan kullanılabilir.

---

## İçindekiler

- [Proje Amacı](#proje-amacı)
- [Genel Mimari](#genel-mimari)
- [Temel Özellikler](#temel-özellikler)
- [Kullanılan Model Yaklaşımı](#kullanılan-model-yaklaşımı)
- [Model Servisleme Yaklaşımı](#model-servisleme-yaklaşımı)
- [CTranslate2 Local Inference](#ctranslate2-local-inference)
- [Klasör Yapısı](#klasör-yapısı)
- [API Endpointleri](#api-endpointleri)
- [Async Job ve Worker Akışı](#async-job-ve-worker-akışı)
- [Worker Batchleme](#worker-batchleme)
- [Retry ve Failed Job Yönetimi](#retry-ve-failed-job-yönetimi)
- [Docker ile Çalıştırma](#docker-ile-çalıştırma)
- [Local Geliştirme](#local-geliştirme)
- [Testler](#testler)
- [Environment Değişkenleri](#environment-değişkenleri)
- [Mevcut Kapsam](#mevcut-kapsam)
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
- Model çağırma katmanını farklı inference seçeneklerine hazır hale getirmek
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
                     Mock / CTranslate2 / Triton / Vertex AI
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
- Structured JSON logging
- MockTranslationClient ile hızlı local test
- CTranslate2TranslationClient ile gerçek model inference
- Triton ve Vertex AI için genişletilebilir client iskeletleri
- Docker Compose ile API + Worker + Redis çalıştırma
- Pytest test altyapısı

---

## Kullanılan Model Yaklaşımı

Proje, Mia-Translate/MADLAD tabanlı makine çevirisi kullanımına göre hazırlanmıştır.

Model tarafındaki temel yaklaşım:

- Mektup tarafındaki hedef model: `mektup-mia/Mia-Translate`
- Temel model referansı: `google/madlad400-3b-mt`
- Model tipi: makine çevirisi
- Mimari: T5 encoder-decoder
- Hedef dil formatı: `<2tr>`, `<2en>`, `<2de>` gibi dil tag’leri

Local gerçek inference testlerinde hazır CTranslate2 int8 MADLAD artifact kullanılmıştır:

```text
Heng666/madlad400-3b-mt-ct2-int8
```

Production/app entegrasyonu için önerilen yöntem, resmi `google/madlad400-3b-mt` modelinden kontrollü bir CTranslate2 artifact üretmek ve bu artifact’i Docker volume veya model registry üzerinden backend’e bağlamaktır.

---

## Model Servisleme Yaklaşımı

Projede model çağırma katmanı `TranslationClient` arayüzü üzerinden soyutlanmıştır.

Desteklenen client seçenekleri:

```text
mock
ctranslate2
triton
vertex
```

Aktif client `.env` üzerinden belirlenir:

```env
TRANSLATION_CLIENT=mock
```

### MockTranslationClient

Backend akışını model dosyası gerektirmeden hızlı test etmek için kullanılır.

Örnek çıktı:

```text
[mock-<2en>] Merhaba
```

Pytest testleri varsayılan olarak mock client ile çalışır. Böylece testler hızlı ve deterministik kalır.

### CTranslate2TranslationClient

CTranslate2 tabanlı gerçek model inference için kullanılır.

Bu client, CTranslate2 formatındaki model artifact’i üzerinden gerçek çeviri üretir.

Local testlerde aşağıdaki artifact kullanılmıştır:

```text
Heng666/madlad400-3b-mt-ct2-int8
```

Bu akışla script, Swagger sync translate, Swagger batch translate ve Redis queue + worker async translate testleri başarıyla yapılmıştır.

### TritonTranslationClient

NVIDIA Triton Inference Server entegrasyonu için hazırlanmış client yapısıdır.

Bu client, modelin ayrı bir inference server olarak servis edildiği senaryoda kullanılmak üzere tasarlanmıştır.

### VertexAITranslationClient

Google Cloud Vertex AI endpoint entegrasyonu için hazırlanmış client yapısıdır.

Vertex AI project, location, endpoint ve credential bilgileri sağlandığında aynı `TranslationClient` arayüzü üzerinden gerçek endpoint çağrısı yapılabilecek şekilde genişletilebilir.

---

## CTranslate2 Local Inference

CTranslate2 tabanlı gerçek model inference local ortamda test edilebilir.

ML bağımlılıkları ana backend bağımlılıklarından ayrı tutulur:

```bash
pip install -r requirements-ml.txt
```

CTranslate2 ortam kontrolü:

```powershell
python scripts/check_ctranslate2.py
```

Hazır CT2 int8 MADLAD artifact ile smoke test:

```powershell
python scripts/ct2_madlad_smoke_test.py --text "Merhaba, nasılsın?" --target-lang en --device cpu --compute-type int8
```

Örnek çıktı:

```text
Hi, how are you?
```

Backend üzerinden gerçek model kullanmak için `.env` içinde:

```env
TRANSLATION_CLIENT=ctranslate2
CTRANSLATE2_MODEL_PATH=./models/madlad400-3b-mt-ct2-int8
CTRANSLATE2_DEVICE=cpu
CTRANSLATE2_COMPUTE_TYPE=int8
```

kullanılır.

Bu ayarla Swagger üzerinden sync, batch ve async job akışları gerçek model inference ile test edilebilir.

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
    ctranslate2_client.py
    triton_client.py
    vertex_ai_client.py
    factory.py

  core/
    config.py
    exceptions.py
    logging.py

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

docs/
  model-serving.md

scripts/
  check_ctranslate2.py
  check_hardware.py
  ct2_madlad_smoke_test.py
  inspect_mia_model.py

tests/
docker-compose.yml
requirements.txt
requirements-ml.txt
README.md
```

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

### Readiness Check

```http
GET /ready
```

Servisin iş kabul etmeye hazır olup olmadığını kontrol eder.

Örnek response:

```json
{
  "status": "ready",
  "service": "mia-translate-backend",
  "environment": "local",
  "checks": {
    "config": "ok",
    "translation_client": "mock",
    "redis": "ok",
    "redis_url_configured": true,
    "vertex_configured": false
  }
}
```

### Tekil Çeviri

```http
POST /api/v1/translate
```

Sync veya async modda tekil çeviri isteği alır.

Sync request:

```json
{
  "text": "Merhaba, nasılsın?",
  "source_lang": "tr",
  "target_lang": "en",
  "mode": "sync"
}
```

Mock response örneği:

```json
{
  "request_id": "req_...",
  "mode": "sync",
  "status": "completed",
  "source_lang": "tr",
  "target_lang": "en",
  "translated_text": "[mock-<2en>] Merhaba, nasılsın?",
  "job_id": null
}
```

CTranslate2 response örneği:

```json
{
  "request_id": "req_...",
  "mode": "sync",
  "status": "completed",
  "source_lang": "tr",
  "target_lang": "en",
  "translated_text": "Hi, how are you?",
  "job_id": null
}
```

Async request:

```json
{
  "text": "Merhaba, nasılsın?",
  "source_lang": "tr",
  "target_lang": "en",
  "mode": "async"
}
```

Async response:

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
      "text": "Merhaba, nasılsın?",
      "source_lang": "tr",
      "target_lang": "en"
    },
    {
      "text": "Bugün backend projesi üzerinde çalışıyorum.",
      "source_lang": "tr",
      "target_lang": "de"
    }
  ],
  "mode": "sync"
}
```

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
  "translated_text": "Hi, how are you?",
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

---

## Worker Batchleme

Worker kısa süreli bir bekleme penceresi içinde queue’dan birden fazla job toplayabilir.

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

---

## Retry ve Failed Job Yönetimi

Worker job işlerken hata alırsa retry mekanizması devreye girer.

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

---

## Docker ile Çalıştırma

API, worker ve Redis servislerini birlikte ayağa kaldırmak için:

```bash
docker compose up --build
```

Arka planda çalıştırmak için:

```bash
docker compose up --build -d
```

Container kontrolü:

```bash
docker ps
```

Beklenen container’lar:

```text
mia-translate-api
mia-translate-worker
mia-translate-redis
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Ready check:

```text
http://127.0.0.1:8000/ready
```

Redis queue kontrolü:

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

Backend bağımlılıkları:

```bash
pip install -r requirements.txt
```

ML bağımlılıkları:

```bash
pip install -r requirements-ml.txt
```

Redis çalıştırma:

```bash
docker compose up -d redis
```

API çalıştırma:

```bash
uvicorn app.main:app --reload
```

Worker tek batch:

```bash
python -m app.workers.translation_worker --once
```

Worker sürekli çalışma:

```bash
python -m app.workers.translation_worker
```

---

## Testler

Testleri çalıştırmak için:

```bash
pytest
```

Pytest testleri varsayılan olarak `MockTranslationClient` ile çalışır.

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
- Structured logging
- Mock / CTranslate2 / Triton / Vertex client seçimi

Gerçek model testleri manual/integration test olarak CTranslate2 client ile ayrıca yapılır.

---

- [Security ve CORS](#security-ve-cors)
## Security ve CORS

API endpointleri isteğe bağlı Bearer token auth ile korunabilir.

Auth `.env` üzerinden açılıp kapatılır:

```env
API_AUTH_ENABLED=false
API_BEARER_TOKEN=dev-secret


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

CTRANSLATE2_MODEL_PATH=./models/madlad400-3b-mt-ct2-int8
CTRANSLATE2_DEVICE=cpu
CTRANSLATE2_COMPUTE_TYPE=int8

VERTEX_PROJECT_ID=
VERTEX_LOCATION=
VERTEX_ENDPOINT_ID=
```

Docker Compose içinde API ve Worker Redis’e şu adresle bağlanır:

```env
REDIS_URL=redis://redis:6379/0
```

Local geliştirmede host üzerinden:

```env
REDIS_URL=redis://localhost:6380/0
```

---

## Mevcut Kapsam

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
- Structured logging
- Client factory
- Mock client
- Gerçek CTranslate2 inference client
- Triton ve Vertex AI client yapıları
- Docker ile API + Worker + Redis çalıştırma
- Pytest test altyapısı
- CTranslate2/MADLAD local smoke test scriptleri
- Bearer token auth middleware
- CORS config desteği

---

## Geliştirme Yol Haritası

Sıradaki teknik adımlar:

1. Resmi `google/madlad400-3b-mt` modelinden kontrollü CTranslate2 artifact üretim sürecinin hazırlanması
2. Triton model repository ve input/output şemasının netleştirilmesi
3. Vertex AI deployment notlarının hazırlanması
4. CI/CD test pipeline kurulumu
5. Frontend/app entegrasyonu için örnek client akışının hazırlanması