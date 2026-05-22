# Triton Readiness Guide

Bu doküman, Mia Translate Backend projesinin NVIDIA Triton Inference Server ile nasıl test edileceğini açıklar.

Bu repoda gerçek Triton server çalıştırılmamıştır. Bu repoda Triton için backend client altyapısı, input/output contract ve model repository taslağı hazırlanmıştır.

---

Bu repoda Triton için model repository taslağı ve Python backend runtime örneği hazırlanmıştır.

triton/model_repository/mia_translate/1/model.py dosyası CTranslate2 tabanlı örnek Triton Python backend runtime sağlar. Bu runtime, TEXT, SOURCE_LANG, TARGET_LANG ve TARGET_TAG inputlarını alır; CTranslate2 model artifact’i üzerinden çeviri yapar ve TRANSLATED_TEXT outputunu döndürür.

Gerçek Triton testi için Triton Inference Server ortamında ctranslate2 ve sentencepiece bağımlılıklarının yüklü olması, CTranslate2 model artifact’inin container içine mount edilmesi ve MODEL_PATH değerinin doğru verilmesi gerekir.

Bu dosya backend contract’ının nasıl çalışacağını göstermek için hazırlanmıştır. Gerçek performans ve GPU testi güçlü makine veya cloud ortamında yapılmalıdır.

## Bu repoda hazır olanlar

- `TRANSLATION_CLIENT=triton` ile Triton client seçimi
- `TritonTranslationClient`
- Sync translate desteği
- Batch translate desteği
- Async worker akışında Triton client kullanımı
- Triton HTTP client dependency dosyası: `requirements-triton.txt`
- Triton input/output contract dokümantasyonu
- Model repository taslağı

---

## Yönetici/dev ekip ne sağlamalı?

Gerçek Triton testi için gerekenler:

1. Çalışan Triton Inference Server
2. `mia_translate` isimli Triton modeli
3. Model repository içinde contract’a uygun input/output tanımı
4. `TEXT`, `SOURCE_LANG`, `TARGET_LANG`, `TARGET_TAG` inputlarını okuyup `TRANSLATED_TEXT` outputunu döndüren model runtime
5. Backend `.env` içinde `TRANSLATION_CLIENT=triton`

Triton tarafındaki model bu contract’a uyduğu sürece FastAPI API, batch endpoint ve async worker aynı şekilde çalışır.

---

## Gerekli environment değerleri

```env
TRANSLATION_CLIENT=triton
TRITON_URL=http://localhost:8001
TRITON_MODEL_NAME=mia_translate
TRITON_TIMEOUT_SECONDS=30
```

Not: `TRITON_URL` değeri `http://localhost:8001` veya `localhost:8001` formatında verilebilir.

---

## Backend’in Triton’a gönderdiği input contract

Backend Triton’a dört input tensor gönderir:

```text
TEXT
SOURCE_LANG
TARGET_LANG
TARGET_TAG
```

Input formatı:

```text
TEXT        -> BYTES, shape [batch_size, 1]
SOURCE_LANG -> BYTES, shape [batch_size, 1]
TARGET_LANG -> BYTES, shape [batch_size, 1]
TARGET_TAG  -> BYTES, shape [batch_size, 1]
```

Örnek batch item:

```json
{
  "TEXT": "Merhaba",
  "SOURCE_LANG": "tr",
  "TARGET_LANG": "en",
  "TARGET_TAG": "<2en>"
}
```

---

## Backend’in Triton’dan beklediği output contract

Backend tek output bekler:

```text
TRANSLATED_TEXT
```

Output formatı:

```text
TRANSLATED_TEXT -> BYTES, shape [batch_size, 1]
```

Örnek output:

```json
[
  ["Hello"]
]
```

---

## Model repository taslağı

Triton model repository için önerilen yapı:

```text
triton/
  model_repository/
    mia_translate/
      config.pbtxt
      1/
        model.py
```

Bu repoda gerçek `model.py` uygulanmamıştır. Çünkü modelin Triton üzerinde hangi runtime ile çalıştırılacağı production ortam kararına bağlıdır.

---

## Kurulum

Triton client dependency kurulumu:

```powershell
pip install -r requirements-triton.txt
```

API çalıştırılır:

```powershell
uvicorn app.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

## Sync test

Request:

```json
{
  "text": "Merhaba",
  "source_lang": "tr",
  "target_lang": "en",
  "mode": "sync"
}
```

Beklenen response:

```json
{
  "status": "completed",
  "translated_text": "Hello"
}
```

---

## Async worker testi

Redis çalıştırılır:

```powershell
docker compose up -d redis
```

Async request gönderilir:

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