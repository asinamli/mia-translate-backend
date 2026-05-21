# Vertex AI Test Guide

Bu doküman, Mia Translate Backend projesinin Google Cloud Vertex AI endpoint ile nasıl test edileceğini açıklar.

Backend tarafında Vertex AI entegrasyonu `VertexAITranslationClient` ile hazırlanmıştır. Bu client, mevcut FastAPI API, Redis queue ve worker mimarisini bozmadan Vertex AI endpoint'e prediction isteği gönderebilir.

---

## Bu repoda hazır olanlar

Bu repoda aşağıdaki parçalar hazırdır:

- `TRANSLATION_CLIENT=vertex` ile Vertex client seçimi
- `VertexAITranslationClient`
- Sync translate desteği
- Batch translate desteği
- Async worker akışında Vertex client kullanımı
- Vertex response parse yapısı
- Vertex için ayrı bağımlılık dosyası: `requirements-cloud.txt`

---

## Yöneticinin sağlaması gereken bilgiler

Vertex AI gerçek testi için aşağıdaki bilgiler gerekir:

```env
TRANSLATION_CLIENT=vertex
VERTEX_PROJECT_ID=your-project-id
VERTEX_LOCATION=us-central1
VERTEX_ENDPOINT_ID=your-endpoint-id
```

Bu değerler Google Cloud tarafındaki Vertex AI endpoint bilgilerine göre doldurulmalıdır.

---

## Yöneticinin yapması gereken kurulum

Projeyi GitHub’dan indirdikten sonra:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
pip install -r requirements-cloud.txt
```

Redis gerekiyorsa:

```powershell
docker compose up -d redis
```

---

## Google Cloud yetkilendirmesi

Vertex AI endpoint’e istek atabilmek için Google Cloud credential gerekir.

### Seçenek 1: gcloud ile local login

Yönetici kendi bilgisayarında şunu çalıştırabilir:

```powershell
gcloud auth application-default login
```

### Seçenek 2: Service account ile test

Yönetici bir service account JSON dosyası kullanacaksa PowerShell’de şunu ayarlayabilir:

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\service-account.json"
```

> Not: Service account JSON dosyası repoya eklenmemelidir.

---

## `.env` ayarı

Yönetici `.env` dosyasında şu değerleri doldurmalıdır:

```env
APP_NAME=mia-translate-backend
APP_ENV=local
API_PREFIX=/api/v1

TRANSLATION_CLIENT=vertex

REDIS_URL=redis://localhost:6380/0

API_AUTH_ENABLED=false
API_BEARER_TOKEN=dev-secret

VERTEX_PROJECT_ID=your-project-id
VERTEX_LOCATION=us-central1
VERTEX_ENDPOINT_ID=your-endpoint-id
```

---

## Backend’in Vertex AI endpoint’e gönderdiği request formatı

Backend, Vertex AI endpoint’e şu formatta `instances` gönderir:

```json
[
  {
    "text": "Merhaba",
    "source_lang": "tr",
    "target_lang": "en",
    "target_tag": "<2en>"
  }
]
```

Bu nedenle Vertex tarafındaki model container bu alanları okuyabilmelidir.

---

## Backend’in beklediği Vertex response formatı

Backend, Vertex response içinde `predictions` alanını bekler.

Desteklenen response formatı 1:

```json
[
  "Hello"
]
```

Desteklenen response formatı 2:

```json
[
  {
    "translated_text": "Hello"
  }
]
```

Aşağıdaki alan adları da desteklenir:

```text
translated_text
translation
text
output
```

Endpoint farklı bir format döndürürse sadece `VertexAITranslationClient` içindeki response parse kısmı güncellenmelidir.

---

## Sync test

API çalıştırılır:

```powershell
uvicorn app.main:app --reload
```

Swagger açılır:

```text
http://127.0.0.1:8000/docs
```

Test request:

```json
{
  "text": "Merhaba",
  "source_lang": "tr",
  "target_lang": "en",
  "mode": "sync"
}
```

Beklenen örnek sonuç:

```json
{
  "status": "completed",
  "translated_text": "Hello"
}
```

---

## Async worker testi

Async request:

```json
{
  "text": "Merhaba",
  "source_lang": "tr",
  "target_lang": "en",
  "mode": "async"
}
```

Worker çalıştırılır:

```powershell
python -m app.workers.translation_worker --once
```

Sonuç sorgulanır:

```http
GET /api/v1/jobs/{job_id}
```

Beklenen sonuç:

```json
{
  "status": "completed",
  "translated_text": "Hello"
}
```

---

## Yöneticiye kısa özet

Bu backend Vertex AI endpoint’e bağlanmaya hazırdır.

Yönetici tarafında gerekenler:

1. Google Cloud project id
2. Vertex AI location
3. Vertex AI endpoint id
4. Vertex AI çağrısı yapabilecek credential
5. Endpoint’in yukarıdaki request formatını kabul etmesi
6. Endpoint’in `predictions` içinde desteklenen response formatlarından birini döndürmesi

Bu bilgiler sağlandığında backend `TRANSLATION_CLIENT=vertex` ile Vertex AI üzerinden çeviri test edebilir.