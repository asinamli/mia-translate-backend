from pathlib import Path

from huggingface_hub import snapshot_download


MODEL_ID = "Heng666/madlad400-3b-mt-ct2-int8"
OUTPUT_DIR = Path("models/madlad400-3b-mt-ct2-int8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Model indiriliyor: {MODEL_ID}")
    print(f"Hedef klasör: {OUTPUT_DIR.resolve()}")

    snapshot_download(
        repo_id=MODEL_ID,
        local_dir=str(OUTPUT_DIR),
        local_dir_use_symlinks=False,
    )

    print("Model indirme tamamlandı.")

 
if __name__ == "__main__":
    main()