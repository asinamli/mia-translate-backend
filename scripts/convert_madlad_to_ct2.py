import argparse
import subprocess
import sys
from pathlib import Path


DEFAULT_MODEL = "google/madlad400-3b-mt"
DEFAULT_OUTPUT_DIR = "models/madlad400-3b-mt-ct2-int8-official"


def run_conversion(model: str, output_dir: str, quantization: str) -> None:
    output_path = Path(output_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ct2-transformers-converter",
        "--model",
        model,
        "--output_dir",
        str(output_path),
        "--quantization",
        quantization,
    ]

    print("CTranslate2 conversion başlatılıyor...")
    print(f"Model: {model}")
    print(f"Output dir: {output_path}")
    print(f"Quantization: {quantization}")
    print()
    print("Komut:")
    print(" ".join(command))
    print()

    try:
        subprocess.run(command, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "ct2-transformers-converter bulunamadı. "
            "Önce ML bağımlılıklarını kurun: pip install -r requirements-ml.txt"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"CTranslate2 conversion başarısız oldu. Exit code: {exc.returncode}"
        ) from exc

    print()
    print("Conversion tamamlandı.")
    print(f"Artifact yolu: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert google/madlad400-3b-mt to CTranslate2 format."
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Hugging Face model id.",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Output CTranslate2 artifact directory.",
    )
    parser.add_argument(
        "--quantization",
        default="int8",
        choices=["int8", "int8_float16", "int8_float32", "float16", "float32"],
        help="CTranslate2 quantization type.",
    )

    args = parser.parse_args()

    try:
        run_conversion(
            model=args.model,
            output_dir=args.output_dir,
            quantization=args.quantization,
        )
    except RuntimeError as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()