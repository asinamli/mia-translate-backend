"""
CTranslate2 kurulmuş mu, Python içinde çalışıyor mu, CPU/CUDA tarafında hangi çalışma tiplerini destekliyor, bunu kontrol etmek.
"""
def main() -> None:
    try:
        import ctranslate2
    except ImportError:
        print("CTranslate2 kurulu değil.")
        print("Kurmak için: pip install -r requirements-ml.txt")
        return

    print("CTranslate2 başarıyla import edildi.")
    print(f"CTranslate2 version: {ctranslate2.__version__}")

    cpu_types = ctranslate2.get_supported_compute_types("cpu")
    print(f"CPU desteklenen compute type değerleri: {cpu_types}")

    try:
        cuda_types = ctranslate2.get_supported_compute_types("cuda")
        print(f"CUDA desteklenen compute type değerleri: {cuda_types}")
    except Exception as exc:
        print(f"CUDA kontrolü yapılamadı: {exc}")


if __name__ == "__main__":
    main()