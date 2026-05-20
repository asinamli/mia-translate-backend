import argparse

from huggingface_hub import HfApi


def format_size(size: int | None) -> str:
    if size is None:
        return "unknown"

    gb = size / (1024 ** 3)
    mb = size / (1024 ** 2)

    if gb >= 1:
        return f"{gb:.2f} GB"

    return f"{mb:.2f} MB"


def inspect_model(model_id: str) -> None:
    api = HfApi()
    model_info = api.model_info(model_id)

    print(f"Model: {model_id}")
    print(f"Library: {model_info.library_name}")
    print(f"Tags: {model_info.tags}")
    print()

    total_size = 0

    print("Dosyalar")
    print("--------")

    for sibling in model_info.siblings:
        size = getattr(sibling, "size", None)
        filename = sibling.rfilename

        print(f"{filename} - {format_size(size)}")

        if size:
            total_size += size

    print()
    print(f"Tahmini toplam dosya boyutu: {format_size(total_size)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Hugging Face model files.")
    parser.add_argument(
        "--model",
        default="mektup-mia/Mia-Translate",
        help="Hugging Face model id",
    )

    args = parser.parse_args()
    inspect_model(args.model)


if __name__ == "__main__":
    main()