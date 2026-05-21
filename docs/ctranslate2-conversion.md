# CTranslate2 Conversion Guide

Bu doküman, resmi `google/madlad400-3b-mt` modelinden kontrollü CTranslate2 artifact üretim sürecini açıklar.

Projede şu ana kadar hazır CTranslate2 int8 MADLAD artifact ile local ve Docker ortamında gerçek inference doğrulanmıştır:

```text
Heng666/madlad400-3b-mt-ct2-int8
```

Production/app entegrasyonu için önerilen yöntem ise resmi modelden kontrollü bir CTranslate2 artifact üretmektir:

```text
google/madlad400-3b-mt
  -> CTranslate2 conversion
  -> models/madlad400-3b-mt-ct2-int8
  -> backend CTranslate2TranslationClient
```

---

## Amaç

Bu adımın amacı, üçüncü taraf hazır artifact yerine resmi Google modelinden dönüştürülmüş, kurum tarafından kontrol edilen bir CTranslate2 model klasörü üretmektir.

Bu sayede:

- Model kaynağı net olur.
- Conversion ayarları kayıt altına alınır.
- Aynı artifact farklı ortamlarda tekrar üretilebilir.
- Docker volume veya model registry üzerinden backend’e bağlanabilir.

---

## Gereksinimler

ML bağımlılıkları kurulmalıdır:

```powershell
pip install -r requirements-ml.txt
```

CTranslate2 kurulumu kontrol edilir:

```powershell
python scripts/check_ctranslate2.py
```

---

## Önerilen conversion ayarı

İlk production adayı için önerilen ayar:

```text
source model: google/madlad400-3b-mt
quantization: int8
output dir: models/madlad400-3b-mt-ct2-int8-official
```

Bu artifact, hazır CT2 smoke test artifact’inden ayrı tutulur.

---

## Conversion komutu

Aşağıdaki script conversion komutunu çalıştırır:

```powershell
python scripts/convert_madlad_to_ct2.py `
  --model google/madlad400-3b-mt `
  --output-dir models/madlad400-3b-mt-ct2-int8-official `
  --quantization int8
```

Conversion başarılı olursa output klasöründe CTranslate2 model dosyaları oluşur.

Script, backend’in tokenizer olarak ihtiyaç duyduğu `spiece.model` dosyasını da output klasörüne kopyalayacak şekilde hazırlanmıştır.

Beklenen klasör örneği:

```text
models/
  madlad400-3b-mt-ct2-int8-official/
    config.json
    model.bin
    shared_vocabulary.json
    spiece.model
```

---

## Yönetici için hızlı çalıştırma

Yönetici veya güçlü bir makinede resmi modelden CTranslate2 artifact üretmek için aşağıdaki adımlar izlenir.

Önce bağımlılıklar kurulur:

```powershell
pip install -r requirements-ml.txt

---

## Backend’de kullanma

`.env` içinde model yolu güncellenir:

```env
TRANSLATION_CLIENT=ctranslate2
CTRANSLATE2_MODEL_PATH=./models/madlad400-3b-mt-ct2-int8-official
CTRANSLATE2_DEVICE=cpu
CTRANSLATE2_COMPUTE_TYPE=int8
```

API çalıştırılır:

```powershell
uvicorn app.main:app --reload
```

Swagger üzerinden test edilir:

```json
{
  "text": "Merhaba, nasılsın?",
  "source_lang": "tr",
  "target_lang": "en",
  "mode": "sync"
}
```

---

## Docker ile kullanma

Docker runtime’da model klasörü volume olarak bağlandığı için `.env` veya compose override tarafında model path şu şekilde verilebilir:

```env
CTRANSLATE2_MODEL_PATH=/models/madlad400-3b-mt-ct2-int8-official
```

Container içinde `/models` klasörü host tarafındaki `./models` klasörüne bağlanmalıdır.

---

## Not

Bu conversion işlemi büyük model indirme ve dönüştürme yaptığı için disk, RAM ve işlem süresi gerektirir. Local geliştirme bilgisayarında çalıştırmak zorunda değildir. Daha güçlü bir makinede üretilen artifact, backend’e Docker volume veya model registry üzerinden bağlanabilir.

Bu projede hazır CT2 artifact ile gerçek inference doğrulanmıştır. Bu dokümandaki süreç, resmi modelden kontrollü artifact üretmek isteyen üretim ortamı için hazırlanmıştır.