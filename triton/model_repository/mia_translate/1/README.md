# Triton Model Version Directory

Bu klasör Triton model version directory taslağıdır.

Gerçek Triton Python backend kullanılacaksa bu klasöre `model.py` eklenir.

Beklenen model davranışı:

- `TEXT`
- `SOURCE_LANG`
- `TARGET_LANG`
- `TARGET_TAG`

inputlarını okuyup:

- `TRANSLATED_TEXT`

outputunu üretmek.

Bu repoda gerçek model runtime bilinçli olarak eklenmemiştir. Çünkü production ortamında modelin Python backend, custom backend veya başka bir runtime ile servis edilmesi yönetici/dev ekip kararıdır.