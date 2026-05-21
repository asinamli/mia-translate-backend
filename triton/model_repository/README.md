# Triton Model Repository

Bu klasör, Mia Translate modelinin NVIDIA Triton Inference Server üzerinde servis edilmesi için önerilen model repository taslağını içerir.

Bu repoda gerçek Triton model runtime uygulanmamıştır. Buradaki amaç, backend ile Triton arasında kullanılacak model adı, input tensor isimleri ve output tensor ismini netleştirmektir.

Model adı:

```text
mia_translate
```

Backend tarafındaki client:

```text
TritonTranslationClient
```

Detaylı açıklama:

```text
docs/triton-readiness.md
```