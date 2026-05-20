# Model Serving Notes

Bu doküman, Mia Translate Backend projesinde model servisleme yaklaşımını açıklar.

Backend mimarisi; API, Redis queue, Redis job store, worker, batchleme ve retry yapıları model çalıştırma yönteminden bağımsız olacak şekilde tasarlanmıştır. Model çağırma katmanı `TranslationClient` arayüzü üzerinden soyutlanmıştır.

Bu sayede aynı backend akışı farklı model servisleme yöntemleriyle çalışabilir:

```text
FastAPI API
  -> TranslationService
  -> TranslationClient
      -> MockTranslationClient
      -> CTranslate2TranslationClient
      -> TritonTranslationClient
      -> VertexAITranslationClient
```

---

## Client Seçimi

Aktif model client `.env` üzerinden belirlenir:

```env
TRANSLATION_CLIENT=mock
```

Desteklenen değerler:

```text
mock
ctranslate2
triton
vertex
```

---

## MockTranslationClient

`MockTranslationClient`, backend akışını gerçek model çalıştırmadan test etmek için kullanılır.

Kullanım amacı:

- API endpointlerini hızlı test etmek
- Validation, queue, worker, retry ve batchleme akışlarını model bağımlılığı olmadan doğrulamak
- Pytest testlerini hızlı ve deterministik tutmak
- CI/CD veya farklı geliştirici ortamlarında model dosyası gerektirmeden test çalıştırmak

Örnek çıktı:

```text
[mock-<2en>] Merhaba
```

Pytest testleri varsayılan olarak mock client ile çalışacak şekilde yapılandırılmıştır.

---

## CTranslate2TranslationClient

`CTranslate2TranslationClient`, CTranslate2 formatındaki MADLAD/Mia tabanlı model artifact’i ile gerçek çeviri inference yapmak için kullanılır.

Local smoke test aşamasında hazır CTranslate2 int8 MADLAD artifact kullanılmıştır:

```text
Heng666/madlad400-3b-mt-ct2-int8
```

Bu artifact ile aşağıdaki akışlar başarıyla doğrulanmıştır:

- Script üzerinden doğrudan CTranslate2 inference
- Swagger üzerinden sync translate
- Swagger üzerinden batch translate
- Redis queue + worker üzerinden async translate
- Worker micro-batch ile birden fazla job işleme

Örnek local `.env` ayarı:

```env
TRANSLATION_CLIENT=ctranslate2
CTRANSLATE2_MODEL_PATH=./models/madlad400-3b-mt-ct2-int8
CTRANSLATE2_DEVICE=cpu
CTRANSLATE2_COMPUTE_TYPE=int8
```

Bu ayarla backend gerçek model inference üzerinden cevap üretir.

---

## Local CTranslate2 Smoke Test

ML bağımlılıkları ayrı tutulur:

```powershell
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

Farklı dil örnekleri:

```powershell
python scripts/ct2_madlad_smoke_test.py --text "Bugün backend projesi üzerinde çalışıyorum." --target-lang de --device cpu --compute-type int8

python scripts/ct2_madlad_smoke_test.py --text "I am testing the translation backend." --target-lang tr --device cpu --compute-type int8
```

---

## Backend Üzerinden CTranslate2 Kullanımı

`.env` içinde client seçimi yapılır:

```env
TRANSLATION_CLIENT=ctranslate2
CTRANSLATE2_MODEL_PATH=./models/madlad400-3b-mt-ct2-int8
CTRANSLATE2_DEVICE=cpu
CTRANSLATE2_COMPUTE_TYPE=int8
```

API çalıştırılır:

```powershell
uvicorn app.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Sync test request:

```json
{
  "text": "Merhaba, nasılsın?",
  "source_lang": "tr",
  "target_lang": "en",
  "mode": "sync"
}
```

Beklenen örnek response:

```json
{
  "mode": "sync",
  "status": "completed",
  "source_lang": "tr",
  "target_lang": "en",
  "translated_text": "Hi, how are you?"
}
```

Async test için Redis çalışmalıdır:

```powershell
docker compose up -d redis
```

Async request sonrası worker çalıştırılır:

```powershell
python -m app.workers.translation_worker --once
```

Worker, Redis queue’dan job’ı alır, CTranslate2 client ile çevirir ve job sonucunu Redis job store’a `completed` olarak yazar.

---

## Production Model Artifact Yaklaşımı

Local smoke test için hazır CTranslate2 int8 MADLAD artifact kullanılmıştır.

Production/app entegrasyonu için önerilen yöntem:

```text
Resmi google/madlad400-3b-mt modelinden kontrollü CTranslate2 artifact üretmek
  -> artifact’i Docker volume veya model registry üzerinden backend’e bağlamak
  -> CTranslate2TranslationClient ile kullanmak
```

Bu yaklaşımda model artifact üretim süreci daha kontrollü, tekrarlanabilir ve deployment ortamına daha uygun olur.

Hazır CT2 artifact, ilk local doğrulama ve backend entegrasyon testi için kullanılmıştır. Production tarafında mümkünse resmi modelden üretilen kurum kontrollü artifact tercih edilmelidir.

---

## Triton Yaklaşımı

Triton, modelin ayrı bir inference server üzerinden servis edilmesi için değerlendirilen seçenektir.

Olası akış:

```text
FastAPI / Worker
  -> TritonTranslationClient
  -> NVIDIA Triton Server
  -> Model runtime
```

Bu yaklaşımda backend doğrudan model dosyası yüklemek yerine Triton endpoint’ine istek atar.

Triton tarafında model repository yapısı, input/output şeması ve runtime seçimi netleştirildiğinde `TritonTranslationClient` gerçek inference çağrısı yapacak şekilde genişletilebilir.

---

## Vertex AI Yaklaşımı

Vertex AI, modelin Google Cloud üzerinde endpoint olarak yayınlanması için kullanılabilecek deployment seçeneğidir.

Olası akış:

```text
FastAPI / Worker
  -> VertexAITranslationClient
  -> Vertex AI Endpoint
  -> Model container
```

Vertex AI kullanımı için project, location, endpoint ve credential bilgileri gerekir. Bu yüzden local geliştirme sürecinde mock veya CTranslate2 client kullanılır.

---

## Test Stratejisi

Projede testler iki ana gruba ayrılır:

```text
Unit test / pytest:
  Mock client ile hızlı ve deterministik testler

Manual / integration test:
  CTranslate2 client ile gerçek model inference testleri
```

Bu ayrım sayesinde backend testleri model dosyasına bağlı kalmadan çalışabilir. Gerçek model testleri ise local ortamda ayrıca doğrulanır.